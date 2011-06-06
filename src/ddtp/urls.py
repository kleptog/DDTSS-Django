
from django.conf.urls.defaults import patterns, include, handler500, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

from ddtp.ddt import views as ddt_views

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    url(r'^$', ddt_views.index, name='ddt_index'),
    url(r'^(\w).html', ddt_views.browse, name='ddt_overview'),
    url(r'^package/([\w.+-]+)$', ddt_views.package, name='ddt_package'),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
