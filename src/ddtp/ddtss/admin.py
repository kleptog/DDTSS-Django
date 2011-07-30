# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import hashlib
import string
import random
import time

from django import forms
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib import messages
from ddtp.database.ddtss import with_db_session, Languages, PendingTranslation, PendingTranslationReview, Users
from ddtp.ddtss.views import show_message_screen, get_user

@with_db_session
def view_admin(session, request):
    """ Handle the super admin page """

    user = get_user(request, session)

    if not user.superuser:
        return HttpResponseForbidden('<h1>Forbidden</h1>')

    langs = session.query(Languages).all()
    admins = session.query(Users).filter_by(superuser=True).all()

    context = {
        'languages': langs,
        'admins': admins,
    }
    return render_to_response("ddtss/admin.html", context,
                              context_instance=RequestContext(request))

