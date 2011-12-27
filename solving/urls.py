from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    url(r'^callin$', 'hunt.solving.views.callin', name='callin'),
    url(r'^general$', 'hunt.solving.views.general', name='general'),
)
