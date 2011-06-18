
from django.conf.urls.defaults import patterns, include, handler500, url
from django.conf import settings

from ddtp.ddtss import views as ddtss_views

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    url(r'^$', ddtss_views.view_index, name='ddtss_index'),
    url(r'^xx$', ddtss_views.view_index),
    url(r'^(\w+)$', ddtss_views.view_index_lang, name='ddtss_index_lang'),
    url(r'^(\w+)/translate/(\d+)$', ddtss_views.view_translate, name='ddtss_translate'),
)
