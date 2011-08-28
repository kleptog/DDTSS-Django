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
from django.http import Http404
from django.template import RequestContext
from django.contrib import messages
from ddtp.database.ddtss import with_db_session, Languages, PendingTranslation, PendingTranslationReview, Users, UserAuthority, DescriptionMilestone
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
        'user': user,
    }
    return render_to_response("ddtss/admin.html", context,
                              context_instance=RequestContext(request))

class LanguageAdminForm(forms.Form):
    """
    A form that manages the superuser view of languages
    """

    def __init__(self, session, *args, **kwargs):
        super(LanguageAdminForm, self).__init__(*args, **kwargs)

    language = forms.RegexField(label='Language code', regex=r'^\w\w(_\w\w)?$', help_text="Language code")
    name = forms.CharField(label="Name", max_length=30, help_text = "Human understandable name for language.")
    enabled = forms.BooleanField(label="Enabled", required=False, help_text="Enabled for DDTSS")

@with_db_session
def view_admin_lang(session, request, language):
    """ Handle superuser language management """

    user = get_user(request, session)

    if not user.superuser:
        return HttpResponseForbidden('<h1>Forbidden</h1>')

    # Note: this is one of the few places where you're allowed to look at a disable language
    lang = session.query(Languages).get(language)
    if not lang:
        raise Http404()

    if request.method == "POST":
        if 'cancel' in request.POST:
            return redirect('ddtss_admin')
        if 'submit' in request.POST:
            form = LanguageAdminForm(session,data=request.POST)
            if form.is_valid():
                # Modify language
                lang.fullname = form.cleaned_data['name']
                lang.enabled_ddtss = form.cleaned_data['enabled']

                session.commit()

                return redirect('ddtss_admin')
        if 'add' in request.POST:
            # Add user as language coordinator
            new_user = session.query(Users).get(request.POST.get('username'))
            if not new_user:
                messages.error(request, 'User %r not found' % request.POST.get('username'))
            else:
                # User exists, add or update authority
                new_auth = new_user.get_authority(language)
                new_auth.auth_level = UserAuthority.AUTH_LEVEL_COORDINATOR
                session.add(new_auth)
                messages.info(request, 'User %s now coordinator' % new_user.username)
                session.commit()
        if 'del' in request.POST:
            # Remove user as language coordinator
            new_user = session.query(Users).get(request.POST.get('del'))
            if not new_user:
                messages.error(request, 'User %r not found' % request.POST.get('username'))
            else:
                # User exists, drop back to trusted user
                new_auth = new_user.get_authority(language)
                new_auth.auth_level = UserAuthority.AUTH_LEVEL_TRUSTED
                messages.info(request, 'User %s now only trusted' % new_user.username)
                session.commit()

    form = LanguageAdminForm(session,dict( \
        language=language, \
        name=lang.fullname, \
        enabled=lang.enabled_ddtss \
        ))

    return render_to_response("ddtss/admin_lang.html", { 'lang': lang, 'form': form },
                              context_instance=RequestContext(request))

class CoordinatorAdminForm(forms.Form):
    """
    A form that manages the superuser view of languages
    """
    error_css_class = 'error'

    milestone_high = forms.ChoiceField(label="1. Milestone", required=False, help_text="1. Milestone");
    milestone_medium = forms.ChoiceField(label="2. Milestone", required=False, help_text="2. Milestone");
    milestone_low = forms.ChoiceField(label="3. Milestone", required=False, help_text="3. Milestone");

    ct = forms.IntegerField(min_value=-1, max_value=10, initial=1, help_text="Points for coordinator translation")
    lt = forms.IntegerField(min_value=-1, max_value=10, initial=1, help_text="Points for logged-in translation")
    at = forms.IntegerField(min_value=-1, max_value=10, initial=1, help_text="Points for anonymous translation")
    cr = forms.IntegerField(min_value=-1, max_value=10, initial=1, help_text="Points for coordinator review")
    lr = forms.IntegerField(min_value=-1, max_value=10, initial=1, help_text="Points for logged-in review")
    ar = forms.IntegerField(min_value=-1, max_value=10, initial=1, help_text="Points for anonymous review")

    stable = forms.IntegerField(min_value=0, max_value=10, initial=1, help_text="Points for no changes")
    accept = forms.IntegerField(min_value=1, max_value=99, initial=3, help_text="Points required for acceptence")

    # Set class of field to integer input
    ct.widget.attrs['class'] = 'intinput'
    lt.widget.attrs['class'] = 'intinput'
    at.widget.attrs['class'] = 'intinput'
    cr.widget.attrs['class'] = 'intinput'
    lr.widget.attrs['class'] = 'intinput'
    ar.widget.attrs['class'] = 'intinput'
    stable.widget.attrs['class'] = 'intinput'
    accept.widget.attrs['class'] = 'intinput'

    def __init__(self, session, *args, **kwargs):
        super(CoordinatorAdminForm, self).__init__(*args, **kwargs)
        # This little peice of magic sets te class on any field that has an error
        for f_name in self.errors:
            self.fields[f_name].widget.attrs['class'] += ' error'
        self.fields['milestone_high'].choices = [(x, x) for (x,) in ( session.query(DescriptionMilestone.milestone).distinct()) ]
        self.fields['milestone_medium'].choices = [(x, x) for (x,) in ( session.query(DescriptionMilestone.milestone).distinct()) ]
        self.fields['milestone_low'].choices = [(x, x) for (x,) in ( session.query(DescriptionMilestone.milestone).distinct()) ]

    def clean(self):
        data = self.cleaned_data

        # Helper function to check if field f1 >= field f2
        def check(f1, f2):
            if f1 in data and f2 in data:
                if data[f1] < data[f2]:
                    self._errors[f1] = self.error_class([self[f1].help_text + " must be greater of equal to " + self[f2].help_text])

        check('ct', 'lt')
        check('lt', 'at')
        check('cr', 'lr')
        check('lr', 'ar')

        return data

@with_db_session
def view_coordinator(session, request):
    """ Handle coordinator language management """

    user = get_user(request, session)
    language = user.lastlanguage_ref

    auth = user.get_authority(language)

    if auth.auth_level != auth.AUTH_LEVEL_COORDINATOR:
        return HttpResponseForbidden('<h1>Forbidden</h1>')

    lang = session.query(Languages).get(language)
    if not lang or not lang.enabled_ddtss:
        raise Http404()

    form = None
    if request.method == "POST":
        if 'cancel' in request.POST:
            return redirect('ddtss_index_lang', language)
        if 'update' in request.POST:
            form = CoordinatorAdminForm(session,data=request.POST)
            if form.is_valid():
                # Modify language
                lang.milestone_high = form.cleaned_data['milestone_high']
                lang.milestone_medium = form.cleaned_data['milestone_medium']
                lang.milestone_low = form.cleaned_data['milestone_low']
                # This little dance is needed because just changing the model doesn't mark the object dirty
                model = lang.translation_model
                session.expire(lang, ['translation_model'])
                model.from_form_fields(form.cleaned_data)
                lang.translation_model = model

                messages.info(request, 'Translation model configuration updated')
                session.commit()
        if 'add' in request.POST:
            # Add user as language coordinator
            new_user = session.query(Users).get(request.POST.get('username'))
            if not new_user:
                messages.error(request, 'User %r not found' % request.POST.get('username'))
            else:
                # User exists, add or update authority
                new_auth = new_user.get_authority(language)
                new_auth.auth_level = UserAuthority.AUTH_LEVEL_TRUSTED
                session.add(new_auth)
                messages.info(request, 'User %s now trusted' % new_user.username)
                session.commit()
        if 'del' in request.POST:
            # Remove user as language coordinator
            new_user = session.query(Users).get(request.POST.get('del'))
            if not new_user:
                messages.error(request, 'User %r not found' % request.POST.get('username'))
            else:
                # User exists, drop back to trusted user
                new_auth = new_user.get_authority(language)
                new_auth.auth_level = UserAuthority.AUTH_LEVEL_NONE
                messages.info(request, 'User %s no longer trusted' % new_user.username)
                session.commit()

    if not form:
        form_fields = dict(milestone_high=lang.milestone_high,\
                           milestone_medium=lang.milestone_medium,\
                           milestone_low=lang.milestone_low)
        form_fields.update(lang.translation_model.to_form_fields())
        form = CoordinatorAdminForm(session, form_fields)

    return render_to_response("ddtss/coordinator.html", { 'lang': lang, 'form': form },
                              context_instance=RequestContext(request))
