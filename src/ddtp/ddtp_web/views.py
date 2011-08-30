# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from ddtp.database.ddtp import with_db_session, Description, PackageVersion, DescriptionTag, ActiveDescription, Translation, DescriptionMilestone, Part, PartDescription
from ddtp.database.ddtss import PendingTranslation, Languages
from sqlalchemy import func, distinct
from ddtp.ddtss.views import get_user

@cache_page(60*60)   # Cache for an hour
@with_db_session
def view_browse(session, request, prefix):
    """ Does overview pages (<foo>.html) """

    user = get_user(request, session)

    resultset = session.query(PackageVersion.package, PackageVersion.description_id, DescriptionTag). \
                        filter(PackageVersion.description_id==DescriptionTag.description_id). \
                        filter(PackageVersion.package.like(prefix+'%')). \
                        order_by(PackageVersion.package, PackageVersion.description_id, DescriptionTag.tag).all()

    # defaultdict would be better here, but django can't iterate over defaultdicts
    params = dict()
    for package, descr_id, tag in resultset:
        if package not in params:
            params[package] = dict()
        if descr_id not in params[package]:
            params[package][descr_id] = list()
        params[package][descr_id].append(tag)

    # We want this sorted, so we need to flatten this to just lists
    params = [(package,
                  [(descr_id, sorted(tags, key=lambda x:x.tag))
                    for descr_id, tags in sorted(descrs.items())])
               for package,descrs in sorted(params.items())]

    return render_to_response("overview.html", {'packages': params, 'prefix': prefix, 'user': user}, context_instance=RequestContext(request))

@cache_page(60*60)   # Cache for an hour
@with_db_session
def view_index(session, request):
    """ Main index.html, show summary info """

    user = get_user(request, session)
    lang = user.lastlanguage_ref
    if lang is None:
        lang = 'xx'
    if lang != 'xx':
        return redirect('ddtss_index_lang', lang)

    return redirect('ddtss_index')

@with_db_session
def view_package(session, request, package_name):
    """ Show the page for a single package """

    user = get_user(request, session)

    params = dict()
    params['prefixlist'] = map(chr, range(ord('0'), ord('9')+1))
    params['prefixlist'] += map(chr, range(ord('a'), ord('z')+1))

    resultset = session.query(Description, PackageVersion, ActiveDescription.description_id). \
                        filter(PackageVersion.package==package_name). \
                        outerjoin(PackageVersion, PackageVersion.description_id == Description.description_id). \
                        outerjoin(ActiveDescription, ActiveDescription.description_id == Description.description_id). \
                        distinct(-Description.description_id). \
                        order_by(-Description.description_id)

    params['package'] = resultset
    params['package_name'] = package_name
    params['user'] = user

    return render_to_response("package.html", params, context_instance=RequestContext(request))

@with_db_session
def view_descr(session, request, descr_id):
    """ Show the page for a single description """

    user = get_user(request, session)

    params = dict()
    params['prefixlist'] = map(chr, range(ord('0'), ord('9')+1))
    params['prefixlist'] += map(chr, range(ord('a'), ord('z')+1))

    # This description
    descr = session.query(Description). \
                        filter(Description.description_id==descr_id).one()
    params['descr'] = descr

    # FIXME... don't use Description.package
    # Other descriptions for this package
    resultset = session.query(Description). \
                        filter(Description.package==descr.package).all()
    params['other_descriptions'] = resultset

    # All languages
    langs = session.query(Translation.language).group_by(Translation.language).order_by(Translation.language).all()
    params['langs'] = [l[0] for l in langs]
    params['user'] = user

    return render_to_response("descr.html", params, context_instance=RequestContext(request))

@with_db_session
def view_transdescr(session, request, descr_id, lang):
    """ Show the page for a single translated description """

    user = get_user(request, session)

    params = dict()
    params['prefixlist'] = map(chr, range(ord('0'), ord('9')+1))
    params['prefixlist'] += map(chr, range(ord('a'), ord('z')+1))

    # This description
    descr = session.query(Description). \
                        filter(Description.description_id==descr_id).one()
    params['descr'] = descr
    params['lang'] = lang

    translation = session.query(Translation). \
                        filter(Translation.description_id==descr_id). \
                        filter(Translation.language==lang).one()
    params['translation'] = translation
    params['user'] = user

    return render_to_response("transdescr.html", params, context_instance=RequestContext(request))

@with_db_session
def view_part(session, request, part_md5):
    """ Show a single translated part """

    user = get_user(request, session)

    params = dict()

    params['part_md5'] = part_md5

    # This part
    parts = session.query(Part). \
                        filter(Part.part_md5==part_md5).\
                        all()
    params['parts'] = parts

    # list of description
    descrs = session.query(PartDescription.description_id).\
                        filter(PartDescription.part_md5==part_md5).\
                        all()
    params['descrs'] = descrs
    params['user'] = user

    return render_to_response("part.html", params, context_instance=RequestContext(request))

@with_db_session
def view_onepart(session, request, part_md5, lang):
    """ Show a single translated part """

    user = get_user(request, session)

    params = dict()

    params['lang'] = lang
    params['part_md5'] = part_md5

    # This part
    part = session.query(Part.part). \
                        filter(Part.part_md5==part_md5).\
                        filter(Part.language==lang).one()
    params['part'] = part

    # list of translations
    langs = session.query(Part.language). \
                        filter(Part.part_md5==part_md5).all()
    params['langs'] = langs

    # list of description
    descrs = session.query(PartDescription.description_id).\
                        filter(PartDescription.part_md5==part_md5).\
                        all()
    params['descrs'] = descrs
    params['user'] = user

    return render_to_response("onepart.html", params, context_instance=RequestContext(request))

@with_db_session
def view_source(session, request, source_name):
    """ Show the page for a single source package """

    user = get_user(request, session)

    params = dict()
    params['prefixlist'] = map(chr, range(ord('0'), ord('9')+1))
    params['prefixlist'] += map(chr, range(ord('a'), ord('z')+1))

    params['source_name'] = source_name

    # FIXME... don't use Description.package
    # All Packages of this source package
    descriptions = session.query(Description.package). \
                        filter(Description.source==source_name).group_by(Description.package).order_by(Description.package).all()
    params['descriptions'] = descriptions
    params['user'] = user

    return render_to_response("source.html", params, context_instance=RequestContext(request))

@with_db_session
def stats_milestones_lang(session, request):
    """ Does milestones stats page per language """

    user = get_user(request, session)
    language = user.lastlanguage_ref

    if language is None:
        language = 'xx'
    if language == 'xx':
        return redirect('ddtss_index')

    resultset = session.query(DescriptionMilestone.milestone,func.count(Translation.description_id)). \
                        join(Translation, DescriptionMilestone.description_id == Translation.description_id).\
                        filter(Translation.language==language).\
                        group_by(DescriptionMilestone.milestone).order_by(DescriptionMilestone.milestone).all()

    resultset1 = session.query(DescriptionMilestone.milestone,func.count(PendingTranslation.description_id)). \
                        join(PendingTranslation, DescriptionMilestone.description_id == PendingTranslation.description_id).\
                        filter(PendingTranslation.language_ref == language). \
                        group_by(DescriptionMilestone.milestone).order_by(DescriptionMilestone.milestone).all()

    resultset2 = session.query(DescriptionMilestone.milestone,func.count(DescriptionMilestone.description_id)). \
                        group_by(DescriptionMilestone.milestone).order_by(DescriptionMilestone.milestone).all()

    params = dict()
    resultdict = dict(resultset)
    resultdict1 = dict(resultset1)
    params['lang'] = language
    params['user'] = user
    params['milestones'] = [(r[0], {'total': r[1], 'translated': resultdict.get(r[0],0), 'pending': resultdict1.get(r[0],0), 'percent': (resultdict.get(r[0],0)*100/r[1]) } ) for r in resultset2]

    return render_to_response("milestones-lang.html", params, context_instance=RequestContext(request))

@cache_page(60*60)   # Cache for an hour
@with_db_session
def stats_one_milestones_lang(session, request, mile):
    """ Does milestones stats page per language """

    user = get_user(request, session)
    language = user.lastlanguage_ref

    if language is None:
        language = 'xx'
    if language == 'xx':
        return redirect('ddtss_index')

    flot = session.query(DescriptionMilestone).filter(DescriptionMilestone.milestone==mile).all()[0].Get_flot_data(language);

    resultset = session.query(Description). \
                        join(DescriptionMilestone, DescriptionMilestone.description_id == Description.description_id).\
                        filter(DescriptionMilestone.milestone==mile).\
                        order_by(Description.prioritize).all()

    resultset1 = session.query(DescriptionMilestone.description_id,PendingTranslation.description_id). \
                        join(PendingTranslation, DescriptionMilestone.description_id == PendingTranslation.description_id).\
                        filter(PendingTranslation.language_ref==language).\
                        filter(DescriptionMilestone.milestone==mile).\
                        all()

    resultset2 = session.query(DescriptionMilestone.description_id,DescriptionMilestone.description_id). \
                        join(Translation, DescriptionMilestone.description_id == Translation.description_id).\
                        filter(Translation.language==language).\
                        filter(DescriptionMilestone.milestone==mile).\
                        all()

#    resultset2 = session.query(DescriptionMilestone.milestone,func.count(DescriptionMilestone.description_id)). \
#                        filter(DescriptionMilestone.milestone==milestone).\
#                        group_by(DescriptionMilestone.milestone).order_by(DescriptionMilestone.milestone).all()

    params = dict()
    resultdict = dict(resultset2)
    resultdict1 = dict(resultset1)
    params['lang'] = language
    params['user'] = user
    params['milestone'] = mile
    params['flot'] = flot
    params['descriptions'] = [(r, {'translate': resultdict.get(r.description_id,0), 'pending': resultdict1.get(r.description_id,0)}) for r in resultset]

    return render_to_response("one_milestones-lang.html", params, context_instance=RequestContext(request))
