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

import time
import json

from django.http import Http404, HttpResponse
from ddtp.database.db import with_db_session
from ddtp.database.ddtp import DescriptionMilestone
from ddtp.database.ddtss import Languages

from ddtp.ddtss.views import get_user

@with_db_session
def milestone_data(session, request, language, milestone):
    """ Generate the data required for a milestone """
    stat = session.query(DescriptionMilestone).filter(DescriptionMilestone.milestone==milestone).first();
    
    if not stat:
        raise Http404()
    lang = session.query(Languages).get(language)
    if not lang or not lang.enabled_ddtss:
        raise Http404()

    # List of (date, package, total)
    flot_data = stat.raw_flot_data_language(language)
    
    milestone_data = [(time.mktime(date.timetuple())*1000, package, total, 100.0*package/total) for date, package, total in flot_data]

    return HttpResponse(json.dumps(milestone_data), mimetype="application/json")

@with_db_session
def thisuser_data(session, request):
    """ Generate the this user's statistics """

    user = get_user(request, session)

    # List of (date, translated, reviewed)
    flot_data = user.raw_flot_data()
    
    user_data = [(time.mktime(date.timetuple())*1000, translated, reviewed) for date, translated,reviewed in flot_data]

    return HttpResponse(json.dumps(user_data), mimetype="application/json")
