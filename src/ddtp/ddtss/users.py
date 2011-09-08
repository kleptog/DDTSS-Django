# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import hashlib
import string
import random
import time

from django import forms
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib import messages
from ddtp.database.ddtss import with_db_session, Languages, PendingTranslation, PendingTranslationReview, Users, DescriptionMilestone
from ddtp.database.ddtp import with_db_session, CollectionMilestone
from ddtp.ddtss.views import show_message_screen, get_user
from urlparse import urlsplit

class UserCreationForm(forms.Form):
    """
    A form that creates a user, with no privileges, from the given username and password.
    """
    email = forms.EmailField(label='Email address')
    username = forms.RegexField(label="Alias", max_length=30, regex=r'^[\w.@+-]+$',
        help_text = "Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.",
        error_messages = {'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."})
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Retype password", widget=forms.PasswordInput,
        help_text = "Enter the same password as above, for verification.")
    realname = forms.CharField(label='Real Name')

    def __init__(self, session, *args, **kwargs):
        self.session = session
        forms.Form.__init__(self, *args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"]

        if self.session.query(Users).get(username):
            raise forms.ValidationError("A user with that username already exists.")

        return username

    def clean_email(self):
        email = self.cleaned_data["email"]

        if self.session.query(Users).filter_by(email=email).first():
            raise forms.ValidationError("A user with that email address already exists.")

        return email

    def clean_password2(self):
        password1 = self.cleaned_data["password1"]
        password2 = self.cleaned_data["password2"]

        if password1 != password2:
            raise forms.ValidationError("Entered passwords don't match")

        return password1

def generate_random_string(length):
    chars = string.letters + string.digits + "/_"

    return "".join([random.choice(chars) for i in range(length)])

@with_db_session
def view_create_user(session, request):
    """ Handle the user creation """
    if request.method == "POST":
        form = UserCreationForm(session=session, data=request.POST)
        if form.is_valid():
            # Create user and add to database
            user = Users(username=form.cleaned_data['username'],
                         email=form.cleaned_data['email'],
                         realname=form.cleaned_data['realname'],
                         active=False,
                         key=generate_random_string(16),
                         lastseen=int(time.time()))

            user.md5password = hashlib.md5(user.key + form.cleaned_data['password1']).hexdigest()

            session.add(user)
            session.commit()

            # Login user in
            request.session['username'] = form.cleaned_data['username']

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            messages.success(request, "Account successfully created.")
            return redirect('ddtss_index')
    else:
        form = UserCreationForm(session)

    request.session.set_test_cookie()

    context = {
        'form': form,
    }
    return render_to_response("ddtss/create_user.html", context,
                              context_instance=RequestContext(request))

class LoginForm(forms.Form):
    """
    A form for logging in
    """
    username = forms.RegexField(label="Alias", max_length=30, regex=r'^[\w.@+-]+$',
        help_text = "Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.",
        error_messages = {'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."})
    password = forms.CharField(label="Password", widget=forms.PasswordInput,
        help_text = "Enter the same password as above, for verification.")

@with_db_session
def view_login(session, request):
    """ Handle user login """

    if request.method == "POST":
        if request.POST.get('cancel'):
            return redirect('ddtss_index')

        form = LoginForm(data=request.POST)
        if form.is_valid():
            # Check if user is exists and password match
            user = session.query(Users).get(form.cleaned_data['username'])

            if user and user.md5password == hashlib.md5(user.key + form.cleaned_data['password']).hexdigest():
                # Login user in
                request.session['username'] = form.cleaned_data['username']

                messages.success(request, "Login successful.")
                return redirect('ddtss_index')
            else:
                messages.error(request, "Login failed.")
    else:
        form = LoginForm()

    context = {
        'form': form,
    }
    return render_to_response("ddtss/login.html", context,
                              context_instance=RequestContext(request))

def view_logout(request):
    """ Handle user logout """
    if 'username' in request.session:
        # Login user in
        messages.success(request, "Logout successful.")
        del request.session['username']

    response = redirect('ddtss_index')

    response.delete_cookie('ddtssuser')
    return response

class UserPreferenc(forms.Form):
    """
    A form change the user preferenc
    """
    milestone = forms.ChoiceField(label="Milestone", required=False, help_text="personal Milestone")
    realname  = forms.CharField(label="Realname", help_text="your real name")
    password1 = forms.CharField(label="Password", required=False, widget=forms.PasswordInput,
        help_text = "Change Passwort")
    password2 = forms.CharField(label="Retype password", required=False, widget=forms.PasswordInput,
        help_text = "Enter the same password as above, for verification.")

    def __init__(self, session, *args, **kwargs):
        super(UserPreferenc, self).__init__(*args, **kwargs)

        self.fields['milestone'].choices = [(x, x) for (x,) in ( session.query(DescriptionMilestone.milestone).distinct()) ]

    def clean_password2(self):
        password1 = self.cleaned_data["password1"]
        password2 = self.cleaned_data["password2"]

        if password1 != password2:
            raise forms.ValidationError("Entered passwords don't match")

        return password1

@with_db_session
def view_preferenc(session, request):
    """ Handle user login """

    user = get_user(request, session)

    if not user.logged_in:
        return show_message_screen(request, 'Only for login user', 'ddtss_login')

    if request.method == "POST":
        if request.POST.get('cancel'):
            return redirect('ddtss_index')

        form = UserPreferenc(session,data=request.POST)
        if form.is_valid():
            user.milestone=form.cleaned_data['milestone']
            user.realname=form.cleaned_data['realname']

            if (form.cleaned_data['password1']):
                user.md5password = hashlib.md5(user.key + form.cleaned_data['password1']).hexdigest()

            session.commit()
            messages.success(request, "Preferenc changed")
            return redirect('ddtss_index')
    else:
        form_fields = dict(milestone=user.milestone,
                realname=user.realname,
                )
        form = UserPreferenc(session,form_fields)

    collectionmilestones = session.query(CollectionMilestone).\
            filter(CollectionMilestone.nametype==1). \
            filter(CollectionMilestone.name==user.username).all()

    context = {
        'user': user,
        'form': form,
        'collectionmilestones': collectionmilestones,
    }
    return render_to_response("ddtss/user_preference.html", context,
                              context_instance=RequestContext(request))


@with_db_session
def view_addusermilestone(session, request, collectiontype, collection):
    """ Handle user login """

    referer = request.META.get('HTTP_REFERER', None)
    if referer is None:
        redirect_to='ddtss_index'
    try:
        redirect_to = urlsplit(referer, 'http', False)[2]
    except IndexError:
        redirect_to='ddtss_index'

    user = get_user(request, session)

    if not user.logged_in:
        return show_message_screen(request, 'Only for login user', 'ddtss_login')

    collectionmilestone = CollectionMilestone(name=user.username,
        nametype=1,
        collection=collectiontype+':'+collection)
    session.add(collectionmilestone)
    try:
        session.commit()
    except:
        messages.error(request, "Error")

    return redirect(redirect_to)


@with_db_session
def view_delusermilestone(session, request, collection):
    """ Handle user login """

    referer = request.META.get('HTTP_REFERER', None)
    if referer is None:
        redirect_to='ddtss_index'
    try:
        redirect_to = urlsplit(referer, 'http', False)[2]
    except IndexError:
        redirect_to='ddtss_index'

    user = get_user(request, session)

    if not user.logged_in:
        return show_message_screen(request, 'Only for login user', 'ddtss_login')

    collectionmilestone = session.query(CollectionMilestone) \
            .filter(CollectionMilestone.collection==collection) \
            .filter(CollectionMilestone.name==user.username) \
            .filter(CollectionMilestone.nametype==1) \
            .one()

    if collectionmilestone:
        session.delete(collectionmilestone)
        session.commit()

        return redirect(redirect_to)

    return HttpResponseForbidden('<h1>Forbidden</h1>')

