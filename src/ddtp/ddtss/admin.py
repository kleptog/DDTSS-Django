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

class LanguageAdminForm(forms.Form):
    """
    A form that manages the superuser view of languages
    """
    language = forms.RegexField(label='Language code', regex=r'^\w\w(_\w\w)?$', help_text="Language code")
    name = forms.CharField(label="Name", max_length=30, help_text = "Human understandable name for language.")
    enabled = forms.BooleanField(label="Enabled", required=False, help_text="Enabled for DDTSS")

@with_db_session
def view_admin_lang(session, request, language):
    """ Handle superuser language management """

    user = get_user(request, session)

    if not user.superuser:
        return HttpResponseForbidden('<h1>Forbidden</h1>')

    lang = session.query(Languages).get(language)
    if not lang:
        raise Http404()

    if request.method == "POST":
        if 'cancel' in request.POST:
            return redirect('ddtss_admin')
        if 'submit' in request.POST:
            form = LanguageAdminForm(data=request.POST)
            if form.is_valid():
                # Modify language
                lang.fullname = form.cleaned_data['name']
                lang.enabled_ddtss = form.cleaned_data['enabled']

                session.commit()

                return redirect('ddtss_admin')

    form = LanguageAdminForm(dict(language=language, name=lang.fullname, enabled=lang.enabled_ddtss))

    return render_to_response("ddtss/admin_lang.html", { 'lang': lang, 'form': form },
                              context_instance=RequestContext(request))
