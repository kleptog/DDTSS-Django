# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from ddtp.database.ddtp import with_db_session, Description, DescriptionTag, ActiveDescription, Translation
from sqlalchemy import func

@cache_page(60*60)   # Cache for an hour
@with_db_session
def view_browse(session, request, prefix):
    """ Does overview pages (<foo>.html) """
    resultset = session.query(Description.package, Description.description_id, DescriptionTag). \
                        filter(Description.description_id==DescriptionTag.description_id). \
                        filter(Description.package.like(prefix+'%')). \
                        order_by(Description.package, Description.description_id, DescriptionTag.tag).all()

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

    return render_to_response("overview.html", {'packages': params, 'prefix': prefix}, context_instance=RequestContext(request))

@cache_page(60*60)   # Cache for an hour
@with_db_session
def view_index(session, request):
    """ Main index.html, show summary info """
    resultset = session.query(Translation.language, func.count(Translation.description_id), func.count(ActiveDescription.description_id)). \
                        outerjoin(ActiveDescription, ActiveDescription.description_id == Translation.description_id). \
                        group_by(Translation.language).order_by(Translation.language).all()

    params = dict()
    params['languages'] = [(r[0], {'total': r[1], 'active': r[2]}) for r in resultset]
    params['translation_count'] = sum(r[1] for r in resultset)
    params['active_count'] = sum(r[2] for r in resultset)

    result = session.query(func.count(Description.description_id)).one()
    params['description_count'] = result[0]

    params['prefixlist'] = map(chr, range(ord('a'), ord('z')+1))

    return render_to_response("index.html", params, context_instance=RequestContext(request))

@with_db_session
def view_package(session, request, package_name):
    """ Show the page for a single package """
    params = dict()
    params['prefixlist'] = map(chr, range(ord('a'), ord('z')+1))

    resultset = session.query(Description, ActiveDescription.description_id). \
                        filter(Description.package==package_name). \
                        outerjoin(ActiveDescription, ActiveDescription.description_id == Description.description_id). \
                        order_by(Description.description_id)

    params['package'] = resultset
    params['package_name'] = package_name

    return render_to_response("package.html", params, context_instance=RequestContext(request))

@with_db_session
def view_descr(session, request, descr_id):
    """ Show the page for a single description """
    params = dict()
    params['prefixlist'] = map(chr, range(ord('a'), ord('z')+1))

    # This description
    descr = session.query(Description). \
                        filter(Description.description_id==descr_id).one()
    params['descr'] = descr

    # Other descriptions for this package
    resultset = session.query(Description). \
                        filter(Description.package==descr.package).all()
    params['other_descriptions'] = resultset

    # All languages
    langs = session.query(Translation.language).group_by(Translation.language).order_by(Translation.language).all()
    params['langs'] = [l[0] for l in langs]

    return render_to_response("descr.html", params, context_instance=RequestContext(request))

@with_db_session
def view_transdescr(session, request, descr_id, lang):
    """ Show the page for a single translated description """
    params = dict()
    params['prefixlist'] = map(chr, range(ord('a'), ord('z')+1))

    # This description
    descr = session.query(Description). \
                        filter(Description.description_id==descr_id).one()
    params['descr'] = descr
    params['lang'] = lang

    translation = session.query(Translation). \
                        filter(Translation.description_id==descr_id). \
                        filter(Translation.language==lang).one()
    params['translation'] = translation

    return render_to_response("transdescr.html", params, context_instance=RequestContext(request))

@with_db_session
def view_source(session, request, source_name):
    """ Show the page for a single source package """
    params = dict()
    params['prefixlist'] = map(chr, range(ord('a'), ord('z')+1))

    params['source_name'] = source_name

    # All Packages of this source package
    descriptions = session.query(Description.package). \
                        filter(Description.source==source_name).group_by(Description.package).order_by(Description.package).all()
    params['descriptions'] = descriptions

    return render_to_response("source.html", params, context_instance=RequestContext(request))
