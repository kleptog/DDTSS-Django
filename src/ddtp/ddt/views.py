from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page
from ddtp.database.ddtp import get_db_session, Description, DescriptionTag

@cache_page(60*60)   # Cache for an hour
def browse(request, prefix):
    session = get_db_session()
    
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
    
    return render_to_response("overview.html", {'packages': params, 'prefix': prefix})
