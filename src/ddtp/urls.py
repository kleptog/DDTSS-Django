
from django.conf.urls.defaults import patterns, include, handler500, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

from ddtp.ddtp_web import views as ddt_views
from ddtp.ddtss import urls as ddtss_urls

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    url(r'^$', ddt_views.view_index, name='ddt_index'),
    url(r'^(\w).html', ddt_views.view_browse, name='ddt_overview'),
    url(r'^package/([\w.+-]+)$', ddt_views.view_package, name='ddt_package'),
    url(r'^source/([\w.+-]+)$', ddt_views.view_source, name='ddt_source'),
    url(r'^descr/(\d+)$', ddt_views.view_descr, name='ddt_descr'),
    url(r'^stats/milestones/(\w\w(?:_\w\w)?)$', ddt_views.stats_milestones_lang, name='ddt_stats_milestones_lang'),
    url(r'^stats/milestones/(\w\w(?:_\w\w)?)/(.+)$', ddt_views.stats_one_milestones_lang, name='ddt_stats_one_milestones_lang'),
    url(r'^descr/(\d+)/(\w+)$', ddt_views.view_transdescr, name='ddt_transdescr'),
    url(r'^ddtss/', include(ddtss_urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
