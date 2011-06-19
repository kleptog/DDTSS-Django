# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import Http404
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from ddtp.database.ddtp import get_db_session, Description, DescriptionTag, ActiveDescription, Translation
from ddtp.database.ddtss import Languages, PendingTranslation, PendingTranslationReview, Users
from sqlalchemy import func
from sqlalchemy.sql import expression
from sqlalchemy.orm import subqueryload

@cache_page(60*60)   # Cache for an hour
def view_index(request):
    """ Does the main index page for DDTSS, with list of languages and stats """
    session = get_db_session()

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

def get_user(request):
    if 'username' in request.session:
        user = session.query(Users).filter_by(username = request.session['username']).one()
    else:
        user = Users(username=request.META.get('REMOTE_ADDR'))
    return user

def view_index_lang(request, language):
    """ Does the main index page for a single language in DDTSS """
    session = get_db_session()

    lang = session.query(Languages).get(language)
    if not lang:
        raise Http404()

    user = get_user(request)

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

def view_translate(request, language, description_id):
    """ Show the translation page for a description """
    session = get_db_session()

    lang = session.query(Languages).get(language)
    if not lang:
        raise Http404()

    descr = session.query(Description).filter_by(description_id=description_id).first()
    if not descr:
        raise Http404()

    # Select FOR UPDATE, to avoid concurrency issues.
    trans = session.query(PendingTranslation).filter_by(language=lang, description_id=description_id).with_lockmode('update').first()
    if not trans:
        # Maybe in the future we build on the fly?
        raise Http404()

    if trans.state != PendingTranslation.STATE_PENDING_TRANSLATION:
        session.commit()
        return show_message_screen(request, 'Already translated, redirecting to review screen', 'ddtss_forreview', language, description_id)

    user = get_user(request)
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
            trans.unlock()
            session.commit()
            return show_message_screen(request, 'Translation abandoned', 'ddtss_index_lang', language)

        if form.cleaned_data['submit']:
            trans.update_translation(form.cleaned_data['short'], form.cleaned_data['long'])
            trans.comment = form.cleaned_data['comment']
            trans.unlock()
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

def view_review(request, language, description_id):
    """ Show the review page for a description """
    session = get_db_session()

    lang = session.query(Languages).get(language)
    if not lang:
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

    user = get_user(request)

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
            session.commit()
            return show_message_screen(request, 'Translation abandoned', 'ddtss_index_lang', language)

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

    return render_to_response("ddtss/translate.html", dict(
        forreview=True,
        lang=lang,
        descr=descr,
        trans=trans), context_instance=RequestContext(request))
