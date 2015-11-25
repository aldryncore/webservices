from django.conf.urls import patterns, include, url
from webservices.sync import provider_for_django
from api.views import HelloProvider
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', provider_for_django(HelloProvider())),
    url(r'^admin/', include(admin.site.urls)),
)
