
from django.conf.urls import patterns, include, handler500, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

from ddtp.ddtp_web import views as ddt_views
from ddtp.ddtss import urls as ddtss_urls

# Pyflakes
handler500

urlpatterns = patterns(
    '',
    url(r'^$', ddt_views.view_index, name='ddt_index'),
    url(r'^(\w).html', ddt_views.view_browse, name='ddt_overview'),
    url(r'^package/([\w.+-]+)$', ddt_views.view_package, name='ddt_package'),
    url(r'^source/([\w.+-]+)$', ddt_views.view_source, name='ddt_source'),
    url(r'^descr/(\d+)$', ddt_views.view_descr, name='ddt_descr'),
    url(r'^part/(\w+)$', ddt_views.view_part, name='ddt_part'),
    url(r'^part/(\w+)/(\w+)$', ddt_views.view_onepart, name='ddt_onepart'),
    url(r'^stats/milestones/(\w+)$', ddt_views.stats_milestones_lang, name='ddt_stats_milestones_lang'),
    url(r'^stats/milestones/(\w+)/(.+)$', ddt_views.stats_one_milestones_lang, name='ddt_stats_one_milestones_lang'),
    url(r'^descr/(\d+)/(\w+)$', ddt_views.view_transdescr, name='ddt_transdescr'),
    url(r'^ddtss/', include(ddtss_urls)),
    url(r'^robots.txt$', ddt_views.block_robots),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
