# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

from django.conf.urls.defaults import patterns, include, handler500, url
from django.conf import settings

from ddtp.ddtss import views as ddtss_views
from ddtp.ddtss import users as ddtss_users

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    url(r'^$', ddtss_views.view_index, name='ddtss_index'),
    url(r'^xx$', ddtss_views.view_index),
    url(r'^(\w\w(?:_\w\w)?)$', ddtss_views.view_index_lang, name='ddtss_index_lang'),
    url(r'^(\w\w(?:_\w\w)?)/translate/(\d+)$', ddtss_views.view_translate, name='ddtss_translate'),
    url(r'^(\w\w(?:_\w\w)?)/forreview/(\d+)$', ddtss_views.view_review, name='ddtss_forreview'),
    url(r'^createlogin$', ddtss_users.view_create_user, name='ddtss_create_user'),
    url(r'^login$', ddtss_users.view_login, name='ddtss_login'),
    url(r'^logout$', ddtss_users.view_logout, name='ddtss_logout'),
)

