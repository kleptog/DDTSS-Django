
from django.conf.urls.defaults import patterns, include, handler500, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

from ddtp.ddt import views as ddt_views

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    url(r'^$', ddt_views.view_index, name='ddt_index'),
    url(r'^(\w).html', ddt_views.view_browse, name='ddt_overview'),
    url(r'^package/([\w.+-]+)$', ddt_views.view_package, name='ddt_package'),
    url(r'^descr/(\d+)$', ddt_views.view_descr, name='ddt_descr'),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
