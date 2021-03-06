"""
DDTSS-Django - A Django implementation of the DDTP/DDTSS website.
Copyright (C) 2011-2014 Martijn van Oosterhout <kleptog@svana.org>

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

from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from ddtp.database.db import with_db_session
from ddtp.database.ddtp import Description, PackageVersion, DescriptionTag, ActiveDescription, Translation, DescriptionMilestone, Part, PartDescription
from ddtp.database.ddtss import PendingTranslation, Languages
from sqlalchemy import func
from sqlalchemy.orm import subqueryload
from ddtp.ddtss.views import get_user

# Cache for an hour
@cache_page(60*60)
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

# Cache for an hour
@cache_page(60*60)
@with_db_session
def view_index(session, request):
    """ Main index.html, main page """

    langinfo = session.query(Languages, func.count(Translation.translation_id), func.count(ActiveDescription.description_id)). \
                             outerjoin(Translation, Translation.language == Languages.language). \
                             outerjoin(ActiveDescription, ActiveDescription.description_id == Translation.description_id). \
                             group_by(Languages). \
                             order_by(Languages.language).all()

    active = session.query(ActiveDescription).count()
    descriptions = session.query(Description).count()
    return render_to_response("index.html", {'langinfo': langinfo, 'active_count': active, 'description_count': descriptions}, context_instance=RequestContext(request))

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
def stats_milestones_lang(session, request, language):
    """ Does milestones stats page per language """

    user = get_user(request, session)
    lang = session.query(Languages).get(language)
    if not lang:
        raise Http404()

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
    params['lang'] = lang
    params['user'] = user
    params['milestones'] = [(r[0], {'total': r[1], 'translated': resultdict.get(r[0],0), 'pending': resultdict1.get(r[0],0), 'percent': (resultdict.get(r[0],0)*100/r[1]) } ) for r in resultset2]

    return render_to_response("milestones_lang.html", params, context_instance=RequestContext(request))

@with_db_session
def stats_one_milestones_lang(session, request, language, mile):
    """ Does milestones stats page per language """

    user = get_user(request, session)
    lang = session.query(Languages).get(language)
    if not lang:
        raise Http404()

    resultset = session.query(Description). \
                        join(DescriptionMilestone, DescriptionMilestone.description_id == Description.description_id).\
                        filter(DescriptionMilestone.milestone==mile).\
                        order_by(Description.prioritize).\
                        options(subqueryload('package_versions')).\
                        all()

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
    params['lang'] = lang
    params['user'] = user
    params['milestone'] = mile
    params['descriptions'] = [(r, {'translate': resultdict.get(r.description_id,0), 'pending': resultdict1.get(r.description_id,0)}) for r in resultset]

    return render_to_response("one_milestones_lang.html", params, context_instance=RequestContext(request))

def block_robots(request):
    """ A simple robots.txt for when this get made the top-level of a site. Stops a robot requesting every package. """
    return HttpResponse("""
User-agent: *
Disallow: /
""")
