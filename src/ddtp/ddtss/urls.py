"""
DDTSS-Django - A Django implementation of the DDTP/DDTSS website.
Copyright (C) 2011-2015 Martijn van Oosterhout <kleptog@svana.org>
Copyright (C) 2014-2015 Fabio Pirola <fabio@pirola.org>

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

from django.conf.urls import patterns, handler500, url

from ddtp.ddtss import views as ddtss_views
from ddtp.ddtss import users as ddtss_users
from ddtp.ddtss import admin as ddtss_admin
from ddtp.ddtss import flot as ddtss_flot

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    url(r'^$', ddtss_views.view_index, name='ddtss_index'),
    url(r'^(xx)$', ddtss_views.view_index),
    url(r'^(\w\w(?:_\w\w)?)$', ddtss_views.view_index_lang, name='ddtss_index_lang'),
    url(r'^(\w\w(?:_\w\w)?)/translate/(\d+)$', ddtss_views.view_translate, name='ddtss_translate'),
    url(r'^(\w\w(?:_\w\w)?)/forreview/(\d+)$', ddtss_views.view_review, name='ddtss_forreview'),
    url(r'^coordinate/(?P<language>\w\w(?:_\w\w)?)$', ddtss_admin.view_coordinator, name='ddtss_coordinate_lang'),
    url(r'^createlogin$', ddtss_users.view_create_user, name='ddtss_create_user'),
    url(r'^createlogin/verifyemail/(?P<user>[\w.@+-]+)$', ddtss_users.view_create_user_verifyemail, name='ddtss_create_user_verifyemail'),
    url(r'^createlogin/complete$', ddtss_users.view_create_user_complete, name='ddtss_create_user_complete'),
    url(r'^preference$', ddtss_users.view_preference, name='ddtss_preference'),
    url(r'^login$', ddtss_users.view_login, name='ddtss_login'),
    url(r'^login/complete$', ddtss_users.view_login_complete, name='ddtss_login_complete'),
    url(r'^logout$', ddtss_users.view_logout, name='ddtss_logout'),
    url(r'^admin$', ddtss_admin.view_admin, name='ddtss_admin'),
    url(r'^admin/(\w\w(?:_\w\w)?)$', ddtss_admin.view_admin_lang, name='ddtss_admin_lang'),
    url(r'^message/global$',ddtss_views.view_write_message, name='ddtss_message', kwargs={'type': 'global'}),
    url(r'^message/lang/(?P<language>\w\w(?:_\w\w)?)$',ddtss_views.view_write_message, name='ddtss_message_lang', kwargs={'type': 'lang'}),
    url(r'^message/user/(?P<to_user>[\w.@+-]+)$',ddtss_views.view_write_message, name='ddtss_message_user', kwargs={'type': 'user'}),
    url(r'^message/descr/(?P<description>\d+)$',ddtss_views.view_write_message, name='ddtss_message_descr', kwargs={'type': 'descr'}),
    url(r'^message/descrlang/(?P<language>\w\w(?:_\w\w)?)/(?P<description>\d+)$',ddtss_views.view_write_message, name='ddtss_message_descrlang', kwargs={'type': 'descrlang'}),
    url(r'^delmessage/(\d+)$',ddtss_views.view_delmessage, name='ddtss_delmessage'),
    url(r'^addusermilestone/(\w+)/(.+)$',ddtss_users.view_addusermilestone, name='ddtss_addusermilestone'),
    url(r'^delusermilestone/(.+)$',ddtss_users.view_delusermilestone, name='ddtss_delusermilestone'),
    url(r'^addlangmilestone/(\w+)/(.+)$',ddtss_admin.view_addlangmilestone, name='ddtss_addlangmilestone'),
    url(r'^dellangmilestone/(.+)$',ddtss_admin.view_dellangmilestone, name='ddtss_dellangmilestone'),
    url(r'^flot/milestone/(?P<language>\w\w(?:_\w\w)?)/(?P<milestone>.+)$',ddtss_flot.milestone_data, name='ddtss_flot_milestone_data'),
    url(r'^flot/thisuser$',ddtss_flot.thisuser_data, name='ddtss_flot_thisuser_data'),
    url(r'^wordlist/(?P<language>\w\w(?:_\w\w)?)$', (ddtss_views.view_get_wordlist), name='ddtss_wordlist'),
    url(r'^wordlist_page/(?P<language>\w\w(?:_\w\w)?)$', (ddtss_views.view_wordlist_page), name='ddtss_wordlist_page'),
    url(r'^wordlist_page/(?P<language>\w\w(?:_\w\w)?)/add_edit_delete$', (ddtss_views.view_wordlist_add_edit_delete), name='ddtss_wordlist_page_add_edit_delete')
)

