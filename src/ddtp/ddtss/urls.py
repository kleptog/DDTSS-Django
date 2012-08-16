# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

from django.conf.urls.defaults import patterns, include, handler500, url
from django.conf import settings

from ddtp.ddtss import views as ddtss_views
from ddtp.ddtss import users as ddtss_users
from ddtp.ddtss import admin as ddtss_admin

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    url(r'^$', ddtss_views.view_index, name='ddtss_index'),
    url(r'^(xx)$', ddtss_views.view_index),
    url(r'^(\w\w(?:_\w\w)?)$', ddtss_views.view_index_lang, name='ddtss_index_lang'),
    url(r'^(\w\w(?:_\w\w)?)/translate/(\d+)$', ddtss_views.view_translate, name='ddtss_translate'),
    url(r'^(\w\w(?:_\w\w)?)/forreview/(\d+)$', ddtss_views.view_review, name='ddtss_forreview'),
    url(r'^coordinate$', ddtss_admin.view_coordinator, name='ddtss_coordinate'),
    url(r'^createlogin$', ddtss_users.view_create_user, name='ddtss_create_user'),
    url(r'^createlogin/complete$', ddtss_users.view_create_user_complete, name='ddtss_create_user_complete'),
    url(r'^preference$', ddtss_users.view_preference, name='ddtss_preference'),
    url(r'^login$', ddtss_users.view_login, name='ddtss_login'),
    url(r'^login/complete$', ddtss_users.view_login_complete, name='ddtss_login_complete'),
    url(r'^logout$', ddtss_users.view_logout, name='ddtss_logout'),
    url(r'^admin$', ddtss_admin.view_admin, name='ddtss_admin'),
    url(r'^admin/(\w\w(?:_\w\w)?)$', ddtss_admin.view_admin_lang, name='ddtss_admin_lang'),
    url(r'^message/$',ddtss_views.view_write_message, name='ddtss_message'),
    url(r'^delmessage/(\d+)$',ddtss_views.view_delmessage, name='ddtss_delmessage'),
    url(r'^addusermilestone/(\w+)/(.+)$',ddtss_users.view_addusermilestone, name='ddtss_addusermilestone'),
    url(r'^delusermilestone/(.+)$',ddtss_users.view_delusermilestone, name='ddtss_delusermilestone'),
    url(r'^addlangmilestone/(\w+)/(.+)$',ddtss_admin.view_addlangmilestone, name='ddtss_addlangmilestone'),
    url(r'^dellangmilestone/(.+)$',ddtss_admin.view_dellangmilestone, name='ddtss_dellangmilestone'),
)

