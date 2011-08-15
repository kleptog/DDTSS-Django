# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import time
import difflib
import re

from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect
from django.http import Http404
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from ddtp.database.ddtp import with_db_session, Description, DescriptionTag, ActiveDescription, Translation, PackageVersion
from ddtp.database.ddtss import Languages, PendingTranslation, PendingTranslationReview, Users
from sqlalchemy import func
from sqlalchemy.sql import expression
from sqlalchemy.orm import subqueryload

@with_db_session
def view_index(session, request, lang=None):
    """ Does the main index page for DDTSS, with list of languages and stats """
    if lang is None:
        user = get_user(request, session)
        lang = user.lastlanguage_ref
    if lang is None:
        lang = 'xx'
    if lang != 'xx':
        return redirect('ddtss_index_lang', lang)

    pending_translations = session.query(Languages, \
                                         func.sum(expression.case([(PendingTranslation.state==PendingTranslation.STATE_PENDING_TRANSLATION, 1)], else_=0)), \
                                         func.sum(expression.case([(PendingTranslation.state==PendingTranslation.STATE_PENDING_REVIEW, 1)], else_=0))) \
                                  .outerjoin(PendingTranslation) \
                                  .group_by(Languages) \
                                  .all()

    translated = session.query(Languages.language, func.count(Translation.description_id)) \
                        .join(Translation, Translation.language==Languages.language) \
                        .group_by(Languages.language) \
                        .all()

    # Convert (lang,count) pairs to dict
    translated = dict(translated)

    # Combine into one resultset
    params = []
    for row in pending_translations:
        params.append( dict(language=row[0].language,
                            fullname=row[0].fullname,
                            enabled=row[0].enabled_ddtss,
                            pending_translation=row[1],
                            pending_review=row[2],
                            translated=translated.get(row[0].language,0)) )

    # Sort by translated descending
    params.sort(key=lambda x:x['translated'], reverse=True)

    return render_to_response("ddtss/index.html", {'languages': params}, context_instance=RequestContext(request))

def get_user(request, session):
    if 'username' in request.session:
        user = session.query(Users).filter_by(username = request.session['username']).one()
    else:
        user = Users(username=request.META.get('REMOTE_ADDR'))
        user.logged_in = False
        user.countreviews = user.counttranslations = 0

    return user

class FetchForm(forms.Form):
    """ This form is used to encapsulate the results of Fetch request """
    package = forms.CharField(max_length=80)
    force = forms.CharField(required=False)
    _charset_ = forms.CharField(required=False)

@with_db_session
def view_index_lang(session, request, language):
    """ Does the main index page for a single language in DDTSS """
    lang = session.query(Languages).get(language)
    if not lang or not lang.enabled_ddtss:
        raise Http404()

    user = get_user(request, session)

    if user.lastlanguage != lang:
        user.lastlanguage = lang
    user.lastseen = int(time.time())

    if request.method == 'POST':
        form = FetchForm(request.POST)

        if not form.is_valid():
            # Maybe return HTTP 400 - Bad request?
            return show_message_screen(request, 'Bad request %r' % form.errors, 'ddtss_index_lang', language)

        if form.cleaned_data['package']:
            pack = form.cleaned_data['package']
            force = form.cleaned_data['force']
            
            if re.match('^\d+$', pack) :
                description_id=pack
            else :
                # FIXME error, ist package name is not found!
                packageversion=session.query(PackageVersion).filter(PackageVersion.package==pack).\
                        join(ActiveDescription, ActiveDescription.description_id == PackageVersion.description_id).limit(1).first()

                if not packageversion :
                    return show_message_screen(request, 'No Package %s found' % pack, 'ddtss_index_lang', language)

                description_id=packageversion.description_id

            description=session.query(Description).filter(Description.description_id==description_id).first()

            if not description :
                return show_message_screen(request, 'No description-id %s found' % str(description_id), 'ddtss_index_lang', language)

            if language not in description.translation or force:
                trans = session.query(PendingTranslation).filter_by(language=lang, description_id=description_id).with_lockmode('update').first()
                if not trans:
                    trans = PendingTranslation(
                            description_id=description_id,
                            language=lang,
                            firstupdate=int(time.time()),
                            lastupdate=int(time.time()),
                            owner_username=user.username,
                            owner_locktime=int(time.time()),
                            iteration=0,
                            state=0)
                    trans.short, trans.long = PendingTranslation.make_suggestion(description, language)
                    session.add(trans)
                    session.commit()
                    return show_message_screen(request, 'Fetch Package %s (%s)' % (description.package,str(description_id)), 'ddtss_index_lang', language)

            return show_message_screen(request, 'Don\'t fetch Package %s' % (pack), 'ddtss_index_lang', language)

    session.commit()

    # TODO: Don't load actual descriptions
    translations = session.query(PendingTranslation,
                                 func.sum(expression.case([(PendingTranslationReview.username==user.username, 1)], else_=0)).label('reviewed'),
                                 func.count().label('reviews')) \
                          .outerjoin(PendingTranslationReview) \
                          .filter(PendingTranslation.language_ref==language) \
                          .group_by(PendingTranslation) \
                          .options(subqueryload(PendingTranslation.reviews)) \
                          .options(subqueryload(PendingTranslation.description)) \
                          .all()

    pending_translations = []
    pending_review = []
    reviewed = []

    for trans, reviewed_by_me, reviews in translations:
        if trans.state == PendingTranslation.STATE_PENDING_REVIEW:
            if reviewed_by_me or trans.owner_username == user.username:
                reviewed.append(trans)
            else:
                pending_review.append(trans)
        elif trans.state == PendingTranslation.STATE_PENDING_TRANSLATION:
            pending_translations.append(trans)

    reviewed.sort(key=lambda t: t.lastupdate, reverse=True)
    pending_review.sort(key=lambda t: t.lastupdate, reverse=False)
    pending_translations.sort(key=lambda t: t.firstupdate, reverse=False)

    return render_to_response("ddtss/index_lang.html", dict(
        lang=lang,
        user=user,
        auth=user.get_authority(language),
        pending_translations=pending_translations,
        pending_review=pending_review,
        reviewed=reviewed), context_instance=RequestContext(request))

def show_message_screen(request, msg, redirect, *args):
    """ Display a message to user, and redirect to a new page after 5 seconds """
    url = reverse(redirect, args=args)

    response = render_to_response("ddtss/message.html", dict(
        msg=msg,
        url=url),
        context_instance=RequestContext(request))

    response['Refresh'] = '5; ' + request.build_absolute_uri(url)

    return response

class TranslationForm(forms.Form):
    """ This form is used to encapsulate the results of form submission """
    short = forms.CharField(max_length=80)
    long = forms.CharField()
    comment = forms.CharField(required=False)
    submit = forms.CharField(required=False)
    abandon = forms.CharField(required=False)
    _charset_ = forms.CharField(required=False)

@with_db_session
def view_translate(session, request, language, description_id):
    """ Show the translation page for a description """
    lang = session.query(Languages).get(language)
    if not lang or not lang.enabled_ddtss:
        raise Http404()

    descr = session.query(Description).filter_by(description_id=description_id).first()
    if not descr:
        raise Http404()

    user = get_user(request, session)

    # Select FOR UPDATE, to avoid concurrency issues.
    trans = session.query(PendingTranslation).filter_by(language=lang, description_id=description_id).with_lockmode('update').first()
    if not trans:
        trans = PendingTranslation(
                description_id=description_id,
                language=lang,
                firstupdate=int(time.time()),
                lastupdate=int(time.time()),
                owner_username=user.username,
                owner_locktime=int(time.time()),
                iteration=0,
                state=PendingTranslation.STATE_PENDING_TRANSLATION)

        # Make a suggestion for the new translation
        trans.short, trans.long = PendingTranslation.make_suggestion(descr, language)
        session.add(trans)

    if trans.state != PendingTranslation.STATE_PENDING_TRANSLATION:
        session.commit()
        return show_message_screen(request, 'Already translated, redirecting to review screen', 'ddtss_forreview', language, description_id)

    # Try to lock the description, note sets the owner field
    if not trans.trylock(user):
        session.commit()
        return show_message_screen(request, 'Translation locked, try again later', 'ddtss_index_lang', language)

    if request.method == 'POST':
        form = TranslationForm(request.POST)

        if not form.is_valid():
            # Maybe return HTTP 400 - Bad request?
            return show_message_screen(request, 'Bad request %r' % form.errors, 'ddtss_index_lang', language)

        if form.cleaned_data['abandon']:
            trans.comment = form.cleaned_data['comment']
            trans.unlock()
            session.commit()
            return show_message_screen(request, 'Translation abandoned', 'ddtss_index_lang', language)

        if form.cleaned_data['submit']:
            trans.update_translation(form.cleaned_data['short'], form.cleaned_data['long'])
            trans.comment = form.cleaned_data['comment']
            trans.unlock()

            # If no longer pending translation, add one to counter
            if trans.state != PendingTranslation.STATE_PENDING_TRANSLATION:
                user.counttranslations += 1

            session.commit()
            return show_message_screen(request, 'Translation submitted', 'ddtss_index_lang', language)

    if trans.comment is None:
        trans.comment = ""
    if trans.short is None:
        trans.short, trans.long = PendingTranslation.make_suggestion(descr, language)

    session.commit()

    return render_to_response("ddtss/translate.html", dict(
        forreview=False,
        lang=lang,
        descr=descr,
        trans=trans), context_instance=RequestContext(request))

def generate_line_diff(old, new):
    """ Given two lines, generate a diff between them. Intends for short
    descriptions, also used internally for the long descriptions.
    Returns a list of pairs:

    ('new', text) is new
    ('old', text) is removed
    ('', text) is unchanged
    """
    res = []
    matcher = difflib.SequenceMatcher(a=old, b=new)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        print tag, i1, i2, j1, j2
        if tag in ('delete', 'replace'):
            res.append( ('old', old[i1:i2]) )
        if tag in ('insert', 'replace'):
            res.append( ('new', new[j1:j2]) )
        if tag == 'equal':
            res.append( ('', old[i1:i2]) )

    return res

def generate_long_description_diff(old, new):
    """ Given two long descriptions generate a diff between them. This can
    be used between two untranslated descriptions, or two translations.
    Returns a list of pairs:

    ('new', text) is new
    ('old', text) is removed
    ('', text) is unchanged
     """

    old_parts = old.split(" .\n")
    new_parts = new.split(" .\n")

    # First make sure each has equally many parts.  Note we could be smarter
    # here, perhaps putting the empty string elsewhere would give better
    # matches.
    while len(old_parts) < len(new_parts):
        old_parts.append('')
    while len(old_parts) > len(new_parts):
        new_parts.append('')

    print old_parts
    print new_parts
    res = []
    # Then handle each pair of parts seperately
    for i in range(len(old_parts)):
        # We could just let the diff loose on the whole string, but with
        # embedded newlines the results are not really intuitive
        old_lines = old_parts[i].rstrip("\n").split("\n")
        new_lines = new_parts[i].rstrip("\n").split("\n")
        while len(old_lines) < len(new_lines):
            old_lines.append('')
        while len(old_lines) > len(new_lines):
            new_lines.append('')

        print old_lines
        print new_lines

        for j in range(len(old_lines)):
            # Put the newline back on the end
            res.extend( generate_line_diff(old_lines[j], new_lines[j]) )
            res.append( ('', '\n') )

        # Except for the last paragraph, add seperater
        if i != len(old_parts)-1:
            res.append( ('', ' .\n') )

    return res

class ReviewForm(forms.Form):
    """ This form is used to encapsulate the results of form submission """
    short = forms.CharField(max_length=80)
    long = forms.CharField()
    comment = forms.CharField(required=False)
    submit = forms.CharField(required=False)
    accept = forms.CharField(required=False)
    nothing = forms.CharField(required=False)

    _charset_ = forms.CharField(required=False)
    timestamp = forms.IntegerField(required=False)

@with_db_session
def view_review(session, request, language, description_id):
    """ Show the review page for a description """
    lang = session.query(Languages).get(language)
    if not lang or not lang.enabled_ddtss:
        raise Http404()

    descr = session.query(Description).filter_by(description_id=description_id).first()
    if not descr:
        raise Http404()

    # Select FOR UPDATE, to avoid concurrency issues.
    trans = session.query(PendingTranslation).filter_by(language=lang, description_id=description_id).with_lockmode('update').first()
    if not trans:
        raise Http404()

    if trans.state != PendingTranslation.STATE_PENDING_REVIEW:
        session.commit()
        return show_message_screen(request, 'Translation not ready for review', 'ddtss_index_lang', language)

    user = get_user(request, session)

    if request.method == 'POST':
        form = ReviewForm(request.POST)

        if not form.is_valid():
            # Maybe return HTTP 400 - Bad request?
            return show_message_screen(request, 'Bad request %r' % form.errors, 'ddtss_index_lang', language)

        if form.cleaned_data['timestamp'] != trans.lastupdate:
            return show_message_screen(request, 'The translation was updated before submission, please recheck changes', 'ddtss_forreview', language, description_id)

        if form.cleaned_data['nothing']:
            trans.comment = form.cleaned_data['comment']
            session.commit()
            return show_message_screen(request, 'Changed comment only', 'ddtss_index_lang', language)

        if form.cleaned_data['accept']:
            trans.comment = form.cleaned_data['comment']
            # Check if user has already reviewed it
            for r in trans.reviews:
                if r.username == user.username:
                    session.commit()
                    return show_message_screen(request, 'Translation was already reviewed', 'ddtss_index_lang', language)
            # Add to reviewers
            trans.reviews.append( PendingTranslationReview(username=user.username) )
            # count review
            user.countreviews += 1

            session.commit()
            return show_message_screen(request, 'Translation reviewed', 'ddtss_index_lang', language)

        if form.cleaned_data['submit']:
            trans.update_translation(form.cleaned_data['short'], form.cleaned_data['long'])
            trans.comment = form.cleaned_data['comment']
            trans.owner_username = user.username
            # Clear reviews
            for review in trans.reviews:
                session.delete(review)
            session.commit()
            return show_message_screen(request, 'Translation updated, review process restarted', 'ddtss_index_lang', language)


    if trans.comment is None:
        trans.comment = ""

    session.commit()

    diff_short = diff_long = None
    if trans.oldshort and trans.for_display(trans.oldshort) != trans.for_display(trans.short):
        diff_short = generate_line_diff(trans.for_display(trans.oldshort), trans.for_display(trans.short))
    if trans.oldlong and trans.for_display(trans.oldlong) != trans.for_display(trans.long):
        diff_long = generate_long_description_diff(trans.for_display(trans.oldlong), trans.for_display(trans.long))

    return render_to_response("ddtss/translate.html", dict(
        forreview=True,
        diff_short=diff_short,
        diff_long=diff_long,
        lang=lang,
        descr=descr,
        trans=trans), context_instance=RequestContext(request))
