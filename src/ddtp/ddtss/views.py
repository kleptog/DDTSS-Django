"""
DDTSS-Django - A Django implementation of the DDTP/DDTSS website.
Copyright (C) 2011-2014 Martijn van Oosterhout <kleptog@svana.org>
Copyright (C) 2014-2015 Fabio Pirola <fabio@pirola.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import time
import difflib
import re
import logging
import json

from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect
from django.http import Http404, HttpResponseForbidden, HttpResponse
from django.template import RequestContext

from ddtp.database.db import with_db_session
from ddtp.database.ddtp import Description, ActiveDescription, Translation, PackageVersion, DescriptionMilestone
from ddtp.database.ddtss import Languages, PendingTranslation, PendingTranslationReview, Users, Messages, \
    Wordlist
from urlparse import urlsplit
from sqlalchemy import func
from sqlalchemy.sql import expression
from sqlalchemy.orm import subqueryload
from ddtp.ddtss.translationmodel import DefaultTranslationModel


# Get an instance of a logger
logger = logging.getLogger(__name__)

@with_db_session
def view_index(session, request, lang=None):
    """ Does the main index page for DDTSS, with list of languages and stats """
    user = get_user(request, session)
    if lang is None:
        lang = user.lastlanguage_ref
    if lang is None:
        lang = 'xx'
    if lang != 'xx':
        return redirect('ddtss_index_lang', lang)

    pending_translations = session.query(Languages, \
                                         func.sum(expression.case([(PendingTranslation.state == PendingTranslation.STATE_PENDING_TRANSLATION, 1)], else_=0)), \
                                         func.sum(expression.case([(PendingTranslation.state == PendingTranslation.STATE_PENDING_REVIEW, 1)], else_=0))) \
                                  .outerjoin(PendingTranslation) \
                                  .group_by(Languages) \
                                  .all()

    translated = session.query(Languages.language, func.count(Translation.description_id)) \
                        .join(Translation, Translation.language == Languages.language) \
                        .group_by(Languages.language) \
                        .all()

    # Convert (lang,count) pairs to dict
    translated = dict(translated)

    # Combine into one resultset
    languages = []
    total_pending_translation = 0
    total_pending_review = 0
    total_translated = 0
    for row in pending_translations:
        languages.append(dict(language=row[0].language,
                            fullname=row[0].fullname,
                            enabled=row[0].enabled_ddtss,
                            pending_translation=row[1],
                            pending_review=row[2],
                            translated=translated.get(row[0].language, 0)))
        total_pending_translation += row[1]
        total_pending_review += row[2]
        total_translated += translated.get(row[0].language, 0)

    # Sort by translated descending
    #languages.sort(key=lambda x:x['translated'], reverse=True)

    return render_to_response("ddtss/index.html",
                              {'languages': languages,
                               'user': user,
                               'total_pending_translation': total_pending_translation,
                               'total_pending_review': total_pending_review,
                               'total_translated': total_translated},
                              context_instance=RequestContext(request))

def get_user(request, session):
    user = None

    if 'username' in request.session:
        # If logged in, use that user
        user = session.query(Users).filter_by(username=request.session['username']).one()
    elif 'ddtssuser' in request.COOKIES:
        # If persistant cookie is present, get the username from there
        cookie_user = Users.from_cookie(request.COOKIES['ddtssuser'])
        if cookie_user:
            # If we found a persistant cookie, check if it's a real user from the database
            user = session.query(Users).filter_by(username=cookie_user.username).first()
        if user:
            # If found, store in session
            request.session['username'] = cookie_user.username
        else:
            # If not in database, use whatever is in cookie
            user = cookie_user

    if not user:
        # Not found anywhere, make a new user
        user = Users(username=request.META.get('REMOTE_ADDR'))
        user.logged_in = False
        user.countreviews = user.counttranslations = 0

    return user

def save_user(response, user):
    """ Wrapper which save user to response and returns the response """
    cookie = user.to_cookie()

    response.set_cookie('ddtssuser', cookie, max_age=6 * 30 * 86400)
    return response

class FetchForm(forms.Form):
    """ This form is used to encapsulate the results of Fetch request """
    package = forms.CharField(max_length=80, required=False)
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

        if not lang.translation_model.user_allowed(user, language, lang.translation_model.ACTION_TRANSLATE):
            return show_message_screen(request, 'User is not permitted to translate', 'ddtss_index_lang', language)

        pack = form.cleaned_data['package'].strip()
        force = form.cleaned_data['force']

        if pack == '':
            description_id = lang.get_next_to_translate(session)
        elif re.match('^\d+$', pack):
            description_id = int(pack)
        else:
            packageversion = session.query(PackageVersion).filter(PackageVersion.package == pack). \
                                     join(ActiveDescription, ActiveDescription.description_id == PackageVersion.description_id).first()

            if not packageversion:
                return show_message_screen(request, 'No Package %s found' % pack, 'ddtss_index_lang', language)

            description_id = packageversion.description_id

        description = session.query(Description).filter(Description.description_id == description_id).first()

        if not description:
            return show_message_screen(request, 'No description-id %s found' % str(description_id), 'ddtss_index_lang', language)

        if language not in description.translation or force:
            trans = session.query(PendingTranslation).filter_by(language=lang, description_id=description_id).with_lockmode('update').first()
            if not trans:
                message = Messages(
                        message="",
                        actionstring="fetched",
                        to_user=None,
                        language=language,
                        for_description=description_id,
                        from_user=user.username,
                        in_reply_to=None,
                        timestamp=int(time.time()))
                session.add(message)

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
                return show_message_screen(request, 'Fetched package %s (%s)' % (description.package, str(description_id)), 'ddtss_translate', language, str(description_id))

        return show_message_screen(request, 'Package %s already translated (and not forced)' % (pack), 'ddtss_index_lang', language)

    session.commit()

    # TODO: Don't load actual descriptions
    translations = session.query(PendingTranslation,
                                 func.sum(expression.case([(PendingTranslationReview.username == user.username, 1)], else_=0)).label('reviewed'),
                                 func.count().label('reviews')) \
                          .outerjoin(PendingTranslationReview) \
                          .filter(PendingTranslation.language_ref == language) \
                          .group_by(PendingTranslation) \
                          .options(subqueryload(PendingTranslation.reviews)) \
                          .options(subqueryload(PendingTranslation.description)) \
                          .options(subqueryload('description.milestones')) \
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

    global_messages = Messages.global_messages(session) \
                          .order_by(Messages.timestamp.desc()) \
                          .limit(20) \
                          .all()

    team_messages = Messages.team_messages(session, language) \
                          .order_by(Messages.timestamp.desc()) \
                          .limit(20) \
                          .all()

    user_messages = Messages.user_messages(session, user.username) \
                          .order_by(Messages.timestamp.desc()) \
                          .limit(20) \
                          .all()

    milestones = []
    for type, name, milestone in (('user_milestone', 'User', user.milestone),
                                  ('lang_milestone_high', 'Team high', lang.milestone_high),
                                  ('lang_milestone_medium', 'Team medium', lang.milestone_medium),
                                  ('lang_milestone_low', 'Team low', lang.milestone_low)):
        if not milestone:
            continue
        m = session.query(DescriptionMilestone).filter(DescriptionMilestone.milestone == milestone).first()
        if not m:
            continue

        info = m.info_language(lang)
        info['type'] = type
        info['typename'] = name
        milestones.append(info)

    involveddescriptions = [x for x, in Messages.involveddescriptions(session, user.username).all()]
    recently_translated = Messages.recently_translated(session, language).limit(10).all()

    response = render_to_response("ddtss/index_lang.html", dict(
        lang=lang,
        user=user,
        auth=user.get_authority(language),
        pending_translations=pending_translations,
        pending_review=pending_review,
        reviewed=reviewed,
        involveddescriptions=involveddescriptions,
        milestones=milestones,
        recently_translated=recently_translated,
        global_messages=global_messages,
        team_messages=team_messages,
        user_messages=user_messages), context_instance=RequestContext(request))

    return save_user(response, user)

def show_message_screen(request, msg, redirect, *args):
    """ Display a message to user, and redirect to a new page after 5 seconds """
    if redirect == 'close':
        response = render_to_response("ddtss/message.html", dict(
            msg=msg,
            close=True),
            context_instance=RequestContext(request))
    else:
        url = reverse(redirect, args=args)

        response = render_to_response("ddtss/message.html", dict(
            msg=msg,
            close=False,
            url=url),
            context_instance=RequestContext(request))

        response['Refresh'] = '5; ' + request.build_absolute_uri(url)

    return response

class TranslationForm(forms.Form):
    """ This form is used to encapsulate the results of form submission """
    short = forms.CharField(max_length=160)
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

    if not lang.translation_model.user_allowed(user, language, lang.translation_model.ACTION_TRANSLATE):
        return show_message_screen(request, 'User is not permitted to translate', 'ddtss_index_lang', language)

    # Select FOR UPDATE, to avoid concurrency issues.
    trans = session.query(PendingTranslation).filter_by(language=lang, description_id=description_id).with_lockmode('update').first()
    if not trans:
        message = Messages(
                message="",
                actionstring="fetched",
                to_user=None,
                language=language,
                for_description=description_id,
                from_user=user.username,
                in_reply_to=None,
                timestamp=int(time.time()))
        session.add(message)

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
            trans.lastupdate = int(time.time())
            trans.comment = form.cleaned_data['comment']
            trans.unlock()

            # If no longer pending translation, add one to counter
            if trans.state != PendingTranslation.STATE_PENDING_TRANSLATION:
                user.counttranslations += 1

            message = ""
            if trans.comment:
                message = trans.comment
                trans.comment = None

            message = Messages(
                    message=message,
                    actionstring="text updated",
                    to_user=None,
                    language=language,
                    for_description=description_id,
                    from_user=user.username,
                    in_reply_to=None,
                    timestamp=int(time.time()))
            session.add(message)

            session.commit()
            if trans.state != PendingTranslation.STATE_PENDING_TRANSLATION:
                return show_message_screen(request, 'Translation submitted for review', 'ddtss_index_lang', language)
            else:
                return show_message_screen(request, 'Translation saved for further translation', 'ddtss_index_lang', language)

    if trans.comment is None:
        trans.comment = ""
    if trans.short is None:
        trans.short, trans.long = PendingTranslation.make_suggestion(descr, language)

    descr_messages = Messages.description_messages(session, description_id) \
                             .order_by(Messages.timestamp) \
                             .all()
    trans_messages = Messages.translation_messages(session, language, description_id) \
                             .order_by(Messages.timestamp) \
                             .all()

    olddiffs = list()
    for olddescr in descr.get_description_predecessors:
        oneolddiff = dict()
        oneolddiff['id'] = descr.description_id
        oneolddiff['short'] = descr.short()
        oneolddiff['long'] = descr.long()
        oneolddiff['transshort'], oneolddiff['translong'] = PendingTranslation.make_quick_suggestion(descr, language)
        oneolddiff['oldid'] = olddescr.description_id
        oneolddiff['oldshort'] = olddescr.short()
        oneolddiff['oldlong'] = olddescr.long()
        oneolddiff['oldtransshort'], oneolddiff['oldtranslong'] = PendingTranslation.make_quick_suggestion(olddescr, language)
        oneolddiff['diff_short'] = generate_line_diff(oneolddiff['oldshort'], oneolddiff['short'])
        oneolddiff['diff_transshort'] = generate_line_diff(oneolddiff['oldtransshort'], oneolddiff['transshort'])
        oneolddiff['diff_long'] = generate_line_diff(oneolddiff['oldlong'], oneolddiff['long'])
        oneolddiff['diff_translong'] = generate_line_diff(oneolddiff['oldtranslong'], oneolddiff['translong'])
        olddiffs.append(oneolddiff)

    session.commit()

    return render_to_response("ddtss/translate.html", dict(
        user=user,
        forreview=False,
        lang=lang,
        descr=descr,
        trans=trans,
        olddiffs=olddiffs,
        descr_messages=descr_messages,
        trans_messages=trans_messages), context_instance=RequestContext(request))

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
            res.append(('old', old[i1:i2]))
        if tag in ('insert', 'replace'):
            res.append(('new', new[j1:j2]))
        if tag == 'equal':
            res.append(('', old[i1:i2]))

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
            res.extend(generate_line_diff(old_lines[j], new_lines[j]))
            res.append(('', '\n'))

        # Except for the last paragraph, add seperater
        if i != len(old_parts) - 1:
            res.append(('', ' .\n'))

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

    if trans.state == PendingTranslation.STATE_PENDING_TRANSLATION:
        session.commit()
        return show_message_screen(request, 'Still need to translated, redirecting to translation screen', 'ddtss_translate', language, description_id)

    if trans.state != PendingTranslation.STATE_PENDING_REVIEW:
        session.commit()
        return show_message_screen(request, 'Translation not ready for review', 'ddtss_index_lang', language)

    user = get_user(request, session)

    if not lang.translation_model.user_allowed(user, language, lang.translation_model.ACTION_REVIEW):
        return show_message_screen(request, 'User is not permitted to review', 'ddtss_index_lang', language)

    if request.method == 'POST':
        form = ReviewForm(request.POST)

        if not form.is_valid():
            # Maybe return HTTP 400 - Bad request?
            return show_message_screen(request, 'Bad request %r' % form.errors, 'ddtss_index_lang', language)

        if form.cleaned_data['timestamp'] != trans.lastupdate:
            return show_message_screen(request, 'The translation was updated before submission, please recheck changes', 'ddtss_forreview', language, description_id)

        if form.cleaned_data['nothing']:
            trans.comment = form.cleaned_data['comment']

            if trans.comment:
                message = Messages(
                        message=trans.comment,
                        to_user=None,
                        language=language,
                        for_description=description_id,
                        from_user=user.username,
                        in_reply_to=None,
                        timestamp=int(time.time()))
                session.add(message)

                trans.comment = None

            trans.lastupdate = int(time.time())
            session.commit()
            return show_message_screen(request, 'Changed comment only', 'ddtss_index_lang', language)

        if form.cleaned_data['accept']:
            trans.comment = form.cleaned_data['comment']
            # Owner can't review own description
            if user == trans.user:
                session.commit()
                return show_message_screen(request, 'Translation was translated by you', 'ddtss_index_lang', language)

            # Check if user has already reviewed it
            for r in trans.reviews:
                if r.username == user.username:
                    session.commit()
                    return show_message_screen(request, 'Translation was already reviewed', 'ddtss_index_lang', language)
            # Add to reviewers
            trans.reviews.append(PendingTranslationReview(username=user.username))
            # count review
            user.countreviews += 1
            trans.lastupdate = int(time.time())

            message = ""
            if trans.comment:
                message = trans.comment
                trans.comment = None

            message = Messages(
                    message=message,
                    actionstring="reviewed",
                    to_user=None,
                    language=language,
                    for_description=description_id,
                    from_user=user.username,
                    in_reply_to=None,
                    timestamp=int(time.time()))
            session.add(message)

            if lang.translation_model.translation_accepted(trans):
                # Translation has been accepted, yay!
                trans.accept_translation()
                session.commit()
                return show_message_screen(request, 'Translation accepted', 'ddtss_index_lang', language)

            session.commit()
            return show_message_screen(request, 'Translation reviewed', 'ddtss_index_lang', language)

        if form.cleaned_data['submit']:
            trans.update_translation(form.cleaned_data['short'], form.cleaned_data['long'])
            trans.comment = form.cleaned_data['comment']
            trans.owner_username = user.username
            trans.lastupdate = int(time.time())
            # Clear reviews
            for review in trans.reviews:
                session.delete(review)

            message = ""
            if trans.comment:
                message = trans.comment
                trans.comment = None

            message = Messages(
                    message=message,
                    actionstring="text updated",
                    to_user=None,
                    language=language,
                    for_description=description_id,
                    from_user=user.username,
                    in_reply_to=None,
                    timestamp=int(time.time()))
            session.add(message)

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


    descr_messages = Messages.description_messages(session, description_id) \
                             .order_by(Messages.timestamp) \
                             .all()
    trans_messages = Messages.translation_messages(session, language, description_id) \
                             .order_by(Messages.timestamp) \
                             .all()

    olddiffs = list()
    for olddescr in descr.get_description_predecessors:
        oneolddiff = dict()
        oneolddiff['id'] = descr.description_id
        oneolddiff['short'] = descr.short()
        oneolddiff['long'] = descr.long()
        oneolddiff['transshort'], oneolddiff['translong'] = PendingTranslation.make_quick_suggestion(descr, language)
        oneolddiff['oldid'] = olddescr.description_id
        oneolddiff['oldshort'] = olddescr.short()
        oneolddiff['oldlong'] = olddescr.long()
        oneolddiff['oldtransshort'], oneolddiff['oldtranslong'] = PendingTranslation.make_quick_suggestion(olddescr, language)
        oneolddiff['diff_short'] = generate_line_diff(oneolddiff['oldshort'], oneolddiff['short'])
        oneolddiff['diff_transshort'] = generate_line_diff(oneolddiff['oldtransshort'], oneolddiff['transshort'])
        oneolddiff['diff_long'] = generate_line_diff(oneolddiff['oldlong'], oneolddiff['long'])
        oneolddiff['diff_translong'] = generate_line_diff(oneolddiff['oldtranslong'], oneolddiff['translong'])
        olddiffs.append(oneolddiff)

    return render_to_response("ddtss/translate.html", dict(
        user=user,
        forreview=True,
        diff_short=diff_short,
        diff_long=diff_long,
        lang=lang,
        descr=descr,
        trans=trans,
        olddiffs=olddiffs,
        descr_messages=descr_messages,
        trans_messages=trans_messages), context_instance=RequestContext(request))


class MessageForm(forms.Form):
    """ This form is used to encapsulate the results of form submission """
    message = forms.CharField(widget=forms.Textarea, required=True)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput, required=False)


@with_db_session
def view_write_message(session, request, type, language=None, description=None, to_user=None):
    """ write a message to a user """

    user = get_user(request, session)

    # type=global, lang, descr, descrlang, user
    if language is not None:
        lang = session.query(Languages).get(language)
    else:
        lang = None
    if description is not None:
        descr = session.query(Description).get(description)
    else:
        descr = None

    # Now check references
    if type in ('lang', 'descrlang'):
        if not lang:
            raise Http404()
    if type in ('descr', 'descrlang'):
        if not descr:
            raise Http404()

    # Only global & lang have restrictions on who can post them
    if type == 'global':
        if not user.is_superuser:
            return HttpResponseForbidden("Only superusers can send global messages")
    if type == 'lang':
        if not lang:
            raise Http404()
        auth = user.get_authority(language)
        if not auth.is_coordinator:
            return HttpResponseForbidden("Only language coordinators can send team messages")

    if request.method == 'GET':
        form = MessageForm(request.GET)

    if request.method == 'POST':
        form = MessageForm(request.POST)

        if request.POST.has_key('cancel'):
            return show_message_screen(request, 'message canceled' , 'close')

        if form.is_valid() and request.POST.has_key('submit'):
            message = Messages(
                    message=form.cleaned_data['message'],
                    to_user=to_user,
                    language=language,
                    for_description=description,
                    from_user=user.username,
                    in_reply_to=form.cleaned_data['in_reply_to'],
                    timestamp=int(time.time()))

            session.add(message)

            session.commit()
            message_suffix = None
            if type == "global":
                message_suffix = "to all users"
            elif type == "user":
                message_suffix = "to %s" % (to_user)
            elif type == "descr":
                message_suffix = "about description %s (%s)" % (descr.description_id, descr.package)
            elif type == "descrlang":
                message_suffix = "about translation of description %s (%s) in %s" % (
                                     descr.description_id,descr.package, lang.language)
            elif type == "lang":
                message_suffix = "to %s translation team" % (lang.language)
            else:
                message_suffix = "... ??? ..."

            return show_message_screen(request, 'Message sent correctly %s' % (message_suffix)
                                       , 'close')

    return render_to_response("ddtss/post_message.html", dict(
        action=request.get_full_path(),
        type=type,
        language=lang,
        description=descr,
        to_user=to_user,
        user=user,
        form=form,
        ), context_instance=RequestContext(request))

@with_db_session
def view_delmessage(session, request, message_id):
    """ del a message """

    referer = request.META.get('HTTP_REFERER', None)
    if referer is None:
        redirect_to = 'ddtss_index'
    try:
        redirect_to = urlsplit(referer, 'http', False)[2]
    except IndexError:
        redirect_to = 'ddtss_index'

    user = get_user(request, session)

    message = session.query(Messages) \
            .filter(Messages.message_id == message_id) \
            .one()

    auth = user.get_authority(message.language)

    # special, if to_user and for_description set...
    # remove only the to_user
    if (message.to_user and message.for_description) \
            and (user.is_superuser or auth.auth_level == auth.AUTH_LEVEL_COORDINATOR or user.username == message.to_user or user.username == message.from_user):
        message.to_user = None;
        session.commit()

        return redirect(redirect_to)


    # superuser can remove all messages
    # user can remove own message
    if user.is_superuser \
            or user.username == message.to_user \
            or user.username == message.from_user:
        if message.actionstring:
            message.message = ""
        else:
            session.delete(message)
        session.commit()

        return redirect(redirect_to)

    # lang admin can remove team message
    if auth.auth_level == auth.AUTH_LEVEL_COORDINATOR \
            and message.to_user is None \
            and message.description_id is None:
        session.delete(message)
        session.commit()

        return redirect(redirect_to)

    #

    return HttpResponseForbidden('<h1>Forbidden</h1>')

@with_db_session
def view_get_wordlist(session, request, language):
    """ Retrieve worlist for a specific language. """
    lang = session.query(Languages).get(language)

    # Unknown language
    if not lang or not lang.enabled_ddtss:
        raise Http404()

    logger.debug("Load wordlist" \
                " - language[%s] lang[%s]", language, lang)
    db_wordlist = session.query(Wordlist.word,
                                 Wordlist.translation) \
                       .filter(Wordlist.language == lang) \
                       .all()
    session.commit()
    # special, if to_user and for_description set...
    # remove only the to_user
    all_wordlist = {}
    if db_wordlist:
        for word, translation in db_wordlist:
            logger.debug("word[%(word)s] translation[%(translation)s]" % locals())
            all_wordlist[word] = translation

    return HttpResponse(json.dumps(all_wordlist), content_type="application/json")


@with_db_session
def view_wordlist_page(session, request, language):
    """ Show the wordlist page for a language """
    lang = session.query(Languages).get(language)

    # Unknown language
    if not lang or not lang.enabled_ddtss:
        raise Http404()
    
    """ Retrieve and save coordinator flag """
    user = get_user(request, session)

    return render_to_response("ddtss/wordlist_page.html", dict(
        forreview=False,
        lang=lang,
        user=user), context_instance=RequestContext(request))


@with_db_session
def view_wordlist_add_edit_delete(session, request, language):
    user = get_user(request, session)
    if not user.is_coordinator:
        return HttpResponseForbidden()
    
    """ Retrieve worlist for a specific language. """
    lang = session.query(Languages).get(language)

    # Unknown language
    if not lang or not lang.enabled_ddtss:
        raise Http404()
    
    
    """ Check request & input data """
    if not request.is_ajax() \
        or request.method != 'POST' \
        or not request:
        return HttpResponse(status=405)
    
    try:
        data=json.loads(request.body)
    except:
        return HttpResponse(status=412)
    
    if not data \
        or not data['action'] \
        or data['action'] not in ['add', 'edit', 'delete'] \
        or not data['word'] \
        or len(data['word']) < 1 \
        or not data['translation'] \
        or len(data['translation'])<3:
        return HttpResponse(status=422)
    logger.debug("Check if already exists wordlist" \
                " - language[%s] lang[%s] word[%s]", \
                language, lang, data['word'])
    
    current_wordlist = session.query(Wordlist) \
                            .filter(Wordlist.language == lang) \
                            .filter(Wordlist.word == data['word']) \
                            .with_lockmode('update') \
                            .all()
    if data['action'] == 'add':
        if current_wordlist:
            session.commit()
            return HttpResponse(status=409)

        logger.info("Add new word to wordlist" \
                " - username[%s] language[%s] lang[%s] word[%s] translation[%s]", \
                user.username, language, lang, data['word'], data['translation'])
        newWord = Wordlist(language=lang, word=data['word'], translation=data['translation'])
        session.add(newWord)
        session.commit()
        return HttpResponse(status=201)
    if data['action'] == 'edit':
        if not current_wordlist:
            session.commit()
            return HttpResponse(status=409)
        logger.info("Update word to wordlist" \
                " - username[%s] language[%s] lang[%s] word[%s] translation[%s]", \
                user.username, language, lang, data['word'], data['translation'])
        for wordlist_cycle in current_wordlist:
            wordlist_cycle.translation=data['translation']
        session.commit()
        return HttpResponse(status=200)
    
    # Otherwise delete
    if not current_wordlist:
        session.commit()
        return HttpResponse(status=410)
    logger.info("Delete word from wordlist" \
            " - username[%s] language[%s] lang[%s] word[%s] translation[%s]", \
            user.username, language, lang, data['word'], data['translation'])
    for wordlist_cycle in current_wordlist:
        session.delete(wordlist_cycle)
    session.commit()
    return HttpResponse(status=204)
