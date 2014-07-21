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
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.template import RequestContext
from django.contrib import messages
from ddtp.database.db import with_db_session
from ddtp.database.ddtss import Users
from ddtp.database.ddtp import CollectionMilestone, DescriptionMilestone
from ddtp.ddtss.views import show_message_screen, get_user
from urlparse import urlsplit

# Monkey patch for django_openid_consumer
import django.http
django.http.get_host = lambda req: req.get_host()

import django_openid_consumer.views

# Import the logging library.
import logging
# Get an instance of a logger.
logger = logging.getLogger(__name__)

class UserCreationForm(forms.Form):
    """
    A form that creates a user, with no privileges, from the given username and password.
    """
    username = forms.RegexField(label="Username", max_length=30, regex=r'^[\w.@+-]+$',
        help_text = "Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.",
        error_messages = {'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."})
    realname = forms.CharField(label='Real Name')
    openid_url = forms.CharField(label='OpenID URL', required=False)

    email = forms.EmailField(label='Email address', required=False)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, required=False,
        min_length=6, help_text = "Enter the password.")
    password2 = forms.CharField(label="Password", widget=forms.PasswordInput, required=False,
        min_length=6, help_text = "Enter the same password as above, for verification.")

    def __init__(self, session, *args, **kwargs):
        self.session = session
        forms.Form.__init__(self, *args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"]

        if self.session.query(Users).filter_by(username=username, active=True).first():
            raise forms.ValidationError("A user with that username already exists.")

        return username

    def clean(self):
        cleaned_data = super(UserCreationForm, self).clean()

        if cleaned_data.get('openid_url'):
            return cleaned_data
        if not (cleaned_data.get('password1') and cleaned_data.get('password2') and cleaned_data.get('email')):
            raise forms.ValidationError("Must specify either an OpenID or email and passwords.")

        if cleaned_data.get('password1') != cleaned_data.get('password2'):
            self._errors["password2"] = self.error_class(["Entered passwords do not match"])

            del cleaned_data['password1']
            del cleaned_data['password2']

        return cleaned_data

def generate_random_string(length):
    chars = string.letters + string.digits + "/_"

    return "".join([random.choice(chars) for i in range(length)])

@with_db_session
def view_create_user(session, request):
    """ Handle the user creation """
    if request.method == "POST":
        form = UserCreationForm(session=session, data=request.POST)
        if form.is_valid():
            if form.cleaned_data['openid_url']:
                # What we do here is add the username to the session and then
                # run the code as if they did a login request.  Then we run the
                # code as if they did a login.  If the login succeeds we can
                # create the user account.
                request.session['new_user_info'] = (form.cleaned_data['username'], form.cleaned_data['realname'])

                def on_failure(request, message):
                    return render_to_response("ddtss/create_user.html", {'message': message},
                                             context_instance=RequestContext(request))

                return django_openid_consumer.views.begin(request,
                                                          on_failure=on_failure,
                                                          redirect_to=reverse('ddtss_create_user_complete'))
            else:
                user = session.query(Users).filter_by(username=form.cleaned_data['username']).first()

                # User may exist but must not be active (forms checks for
                # that).  Allow reuse of users not active, in case email
                # gets lost.
                if not user:
                    user = Users()

                # Create user and add to database
                user.username=form.cleaned_data['username']
                user.email=form.cleaned_data['email']
                user.realname=form.cleaned_data['realname']
                user.active=False
                user.key=generate_random_string(16)
                user.lastseen=int(time.time())
                user.md5password = hashlib.md5(user.key + form.cleaned_data['password1']).hexdigest()

                # User logging in with email address and password
                email = EmailMessage(subject="Verify new DDTSS account",
                                     from_email="ddtss@kleptog.org",
                                     to=[form.cleaned_data['email']],
                                     bcc=["ddtss@kleptog.org"],
                                    )
                confirm_url = request.build_absolute_uri( reverse("ddtss_create_user_verifyemail", args=[form.cleaned_data['username']]) )
                email.body = """
    To confirm your account (%s) on the DDTSS, please follow this link
    %s?key=%s

    If you did not create an account, please ignore this email.
    Django-DDTSS (Debian Distributed Translation Server Satelite)
                """ % (form.cleaned_data['username'], confirm_url, hashlib.md5(user.key).hexdigest())

                email.send()

                session.add(user)
                session.commit()

                messages.success(request, "Verification email sent. Press on contained link to activate account.")
                return redirect("ddtss_index")
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
        return render_to_response("ddtss/create_user.html", {'message': message},
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

        logging.info("User created correctly" \
                     " - username[%(user.username)s]" \
                     " openid[%(user.openid)s]" % locals())
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()

        messages.success(request, "Account successfully created.")
        return redirect('ddtss_index')

    return django_openid_consumer.views.complete(request, on_failure=on_failure, on_success=on_success)

@with_db_session
def view_create_user_verifyemail(session, request, user):
    """ Called for email verification """
    user = session.query(Users).filter_by(username=user).first()

    if not user:
        messages.error(request, "Verification for non-existant user.")
    elif user.active:
        messages.error(request, "User already verified.")
    elif hashlib.md5(user.key).hexdigest() == request.GET.get('key'):
        messages.success(request, "User successfully verified.")
        user.active = True

        # Login user in
        request.session['username'] = user.username

        session.commit()
    else:
        messages.error(request, "Verification failed.")

    return redirect('ddtss_index')


class LoginForm(forms.Form):
    """
    A form for logging in
    """
    username = forms.RegexField(label="Alias", max_length=30, regex=r'^[\w.@+-]+$', required=False,
        help_text = "Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.",
        error_messages = {'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."})
    password = forms.CharField(label="Password", widget=forms.PasswordInput, required=False,
        help_text = "Enter password if no OpenID.")
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

            if user and not user.active:
                # User must have been activated.
                messages.error(request, "Account not yet enabled.")
                success = False
            elif user and user.md5password == hashlib.md5(user.key + form.cleaned_data['password']).hexdigest():
                # Login user in
                request.session['username'] = form.cleaned_data['username']
                logger.info("Login successfully" \
                        " - username[%s]", request.session['username'])
                messages.success(request, "Login successfully.")
                success = True
            else:
                success = False

            # If the user gave an OpenID URL, try to login with that
            def on_failure(request, message):
                messages.error(request, "OpenID login failed: %s" % message)

                # If OpenID and normal login failed, go back to login page
                if not success:
                    return render_to_response("ddtss/login.html", {'form': form},
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
            logger.info("OpenID login successfully" \
                        " - username[%(user.username)s]" % locals())
            messages.success(request, "OpenID login successfully")
        elif 'username' in request.session:
            # User logged in with password as well OpenID
            user = session.query(Users).get(request.session['username'])

            user.openid = request.session['openids'][0].openid
            logger.info("OpenID successfully linked" \
                        " - username[%(user.username)s]" \
                        " openid[%(user.openid)s]" % locals())
            messages.success(request, "OpenID successfully linked with user")
        else:
            messages.error(request, "OpenID successfully linked," \
                           " but no account")

        session.commit()

        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()

        return redirect('ddtss_index')

    return django_openid_consumer.views.complete(request, on_failure=on_failure, on_success=on_success)

@with_db_session
def view_logout(session, request):
    """ Handle user logout """
    user = get_user(request, session)
    if user.logged_in:
        # User logged successfully
        logger.info("Logout successfully" \
                    " - username[%s]", user.username)
        messages.success(request, "Logout successfully.")
        django_openid_consumer.views.signout(request)
        del request.session['username']

    # User not logged in or logged out successfully
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

