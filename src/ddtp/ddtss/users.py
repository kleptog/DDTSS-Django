# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import hashlib
import string
import random
import time

from django import forms
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib import messages
from ddtp.database.ddtss import with_db_session, Languages, PendingTranslation, PendingTranslationReview, Users, DescriptionMilestone
from ddtp.database.ddtp import with_db_session, CollectionMilestone
from ddtp.ddtss.views import show_message_screen, get_user
from urlparse import urlsplit

import django_openid_consumer.views

class UserCreationForm(forms.Form):
    """
    A form that creates a user, with no privileges, from the given username and password.
    """
    username = forms.RegexField(label="Alias", max_length=30, regex=r'^[\w.@+-]+$',
        help_text = "Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.",
        error_messages = {'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."})
    realname = forms.CharField(label='Real Name')
    openid_url = forms.CharField(label='OpenID URL')

    def __init__(self, session, *args, **kwargs):
        self.session = session
        forms.Form.__init__(self, *args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"]

        if self.session.query(Users).get(username):
            raise forms.ValidationError("A user with that username already exists.")

        return username

def generate_random_string(length):
    chars = string.letters + string.digits + "/_"

    return "".join([random.choice(chars) for i in range(length)])

@with_db_session
def view_create_user(session, request):
    """ Handle the user creation """
    if request.method == "POST":
        form = UserCreationForm(session=session, data=request.POST)
        if form.is_valid():
            # What we do here is add the username to the session and then
            # run the code as if they did a login request.  Then we run the
            # code as if they did a login.  If the login succeeds we can
            # create the user account.
            request.session['new_user_info'] = (form.cleaned_data['username'], form.cleaned_data['realname'])

            def on_failure(request, message):
                return render_to_reponse("ddtss/create_user.html", {'message': message},
                                         context_instance=RequestContext(request))

            return django_openid_consumer.views.begin(request,
                                                      on_failure=on_failure,
                                                      redirect_to=reverse('ddtss_create_user_complete'))

    else:
        form = UserCreationForm(session)

    request.session.set_test_cookie()

    context = {
        'form': form,
    }
    return render_to_response("ddtss/create_user.html", context,
                              context_instance=RequestContext(request))

@with_db_session
def view_create_user_complete(session, request):
    """ Called after the OpenID authentication completes """
    def on_failure(request, message):
        request.session.pop('new_user_info',None)
        return render_to_reponse("ddtss/create_user.html", {'message': message},
                                 context_instance=RequestContext(request))

    def on_success(request, identity_url, openid_response):
        if not request.session.get('new_user_info'):
            return on_failure(request, "Failure (no new username)")

        # Setup OpenID middleware (do we really need this?)
        django_openid_consumer.views.default_on_success(request, identity_url, openid_response)

        user = session.query(Users).filter(Users.openid == request.session['openids'][0].openid).first()

        if user:
            messages.error(request, "OpenID already associated with another user, not creating. Logging in instead.")
            request.session['username'] = user.username
            return redirect('ddtss_index')

        # Create user and add to database
        user = Users(username=request.session['new_user_info'][0],
                     email='*',
                     realname=request.session['new_user_info'][1],
                     active=True,
                     key=generate_random_string(16),
                     lastseen=int(time.time()))

        user.md5password = "*"
        user.openid = request.session['openids'][0].openid

        session.add(user)
        session.commit()

        # Login user in
        request.session['username'] = user.username

        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()

        messages.success(request, "Account successfully created.")
        return redirect('ddtss_index')

    return django_openid_consumer.views.complete(request, on_failure=on_failure, on_success=on_success)


class LoginForm(forms.Form):
    """
    A form for logging in
    """
    username = forms.RegexField(label="Alias", max_length=30, regex=r'^[\w.@+-]+$', required=False,
        help_text = "Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.",
        error_messages = {'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."})
    password = forms.CharField(label="Password", widget=forms.PasswordInput, required=False,
        help_text = "Enter the same password as above, for verification.")
    openid_url = forms.CharField(label='OpenID URL', required=False)

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

            # Kill any previous logins
            django_openid_consumer.views.signout(request)
            request.session.pop('username', None)

            if user and user.md5password == hashlib.md5(user.key + form.cleaned_data['password']).hexdigest():
                # Login user in
                request.session['username'] = form.cleaned_data['username']

                messages.success(request, "Login successful.")
                success = True
            else:
                success = False

            # If the user gave an OpenID URL, try to login with that
            def on_failure(request, message):
                messages.error(request, "OpenID login failed: %s" % message)

                # If OpenID and normal login failed, go back to login page
                if not success:
                    return render_to_reponse("ddtss/login.html", {'form': form},
                                             context_instance=RequestContext(request))
                # Otherwise continue, the user is authenticated, albeit without OpenID
                return redirect('ddtss_index')

            if form.cleaned_data['openid_url']:
                return django_openid_consumer.views.begin(request,
                                                          on_failure=on_failure,
                                                          redirect_to=reverse('ddtss_login_complete'))

            if success:
                return redirect('ddtss_index')

            messages.error(request, "Login failed.")
    else:
        form = LoginForm()

    context = {
        'form': form,
    }
    return render_to_response("ddtss/login.html", context,
                              context_instance=RequestContext(request))

@with_db_session
def view_login_complete(session, request):
    """ Called after the OpenID authentication completes """
    def on_failure(request, message):
        messages.error(request, "OpenID login failed: %s" % message)

        if request.session['username']:
            # User is authenticated, without OpenID
            return redirect('ddtss_index')

        return redirect("ddtss_login")

    def on_success(request, identity_url, openid_response):
        # Setup OpenID middleware (do we really need this?)
        django_openid_consumer.views.default_on_success(request, identity_url, openid_response)

        # Try to find user by openid
        user = session.query(Users).filter(Users.openid == request.session['openids'][0].openid).first()

        if user:
            # If found, login user using that
            request.session['username'] = user.username
            messages.success(request, "OpenID login successful")
        elif 'username' in request.session:
            # User logged in with password as well OpenID
            user = session.query(Users).get(request.session['username'])

            user.openid = request.session['openids'][0].openid
            messages.success(request, "OpenID succesfully linked with user")
        else:
            messages.error(request, "OpenID succesful, but no account")

        session.commit()

        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()

        return redirect('ddtss_index')

    return django_openid_consumer.views.complete(request, on_failure=on_failure, on_success=on_success)


def view_logout(request):
    """ Handle user logout """
    if 'username' in request.session:
        # Login user in
        messages.success(request, "Logout successful.")
        del request.session['username']

    django_openid_consumer.views.signout(request)

    response = redirect('ddtss_index')

    response.delete_cookie('ddtssuser')
    return response

class UserPreference(forms.Form):
    """
    A form change the user preference
    """
    milestone = forms.ChoiceField(label="Milestone", required=False, help_text="personal Milestone")
    realname  = forms.CharField(label="Realname", help_text="your real name")
    password1 = forms.CharField(label="Password", required=False, widget=forms.PasswordInput,
        help_text = "Change Passwort")
    password2 = forms.CharField(label="Retype password", required=False, widget=forms.PasswordInput,
        help_text = "Enter the same password as above, for verification.")

    def __init__(self, session, *args, **kwargs):
        super(UserPreference, self).__init__(*args, **kwargs)

        self.fields['milestone'].choices = [(x, x) for (x,) in ( session.query(DescriptionMilestone.milestone).distinct()) ]

    def clean_password2(self):
        password1 = self.cleaned_data["password1"]
        password2 = self.cleaned_data["password2"]

        if password1 != password2:
            raise forms.ValidationError("Entered passwords don't match")

        return password1

@with_db_session
def view_preference(session, request):
    """ Handle user login """

    user = get_user(request, session)

    if not user.logged_in:
        return show_message_screen(request, 'Only for login user', 'ddtss_login')

    if request.method == "POST":
        if request.POST.get('cancel'):
            return redirect('ddtss_index')

        form = UserPreference(session,data=request.POST)
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
        form = UserPreference(session,form_fields)

    collectionmilestones = session.query(CollectionMilestone).\
            filter(CollectionMilestone.nametype==CollectionMilestone.NAME_TYPE_USER). \
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
        nametype=CollectionMilestone.NAME_TYPE_USER,
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
            .filter(CollectionMilestone.nametype==CollectionMilestone.NAME_TYPE_USER) \
            .one()

    if collectionmilestone:
        session.delete(collectionmilestone)
        session.commit()

        return redirect(redirect_to)

    return HttpResponseForbidden('<h1>Forbidden</h1>')

