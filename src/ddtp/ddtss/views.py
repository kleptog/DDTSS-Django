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

def view_index_lang(request, language):
    """ Does the main index page for a single language in DDTSS """
    session = get_db_session()

    lang = session.query(Languages).get(language)
    if not lang:
        raise Http404()

    if 'username' in request.session:
        user = session.query(Users).filter_by(username = request.session['username']).one()
    else:
        user = Users(username=request.META.get('REMOTE_ADDR'))

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
        if reviewed_by_me or trans.owner_username == user.username:
            reviewed.append(trans)
        elif trans.state == PendingTranslation.STATE_PENDING_REVIEW:
            pending_review.append(trans)
        else:
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

def view_translate(request, language, description_id):
    """ Show the translation page for a description """
    session = get_db_session()

    lang = session.query(Languages).get(language)
    if not lang:
        raise Http404()

    descr = session.query(Description).filter_by(description_id=description_id).first()
    if not descr:
        raise Http404()

    trans = session.query(PendingTranslation).filter_by(language=lang, description_id=description_id).first()
    if not trans:
        # Maybe in the future we build on the fly?
        raise Http404()

    if trans.comment is None:
        trans.comment = ""
    if trans.short is None:
        trans.short, trans.long = PendingTranslation.make_suggestion(descr, language)

    return render_to_response("ddtss/translate.html", dict(
        lang=lang,
        descr=descr,
        trans=trans), context_instance=RequestContext(request))
