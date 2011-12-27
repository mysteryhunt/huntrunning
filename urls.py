from django.conf.urls.defaults import patterns, include, url


from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^solving/', include('hunt.solving.urls')),
    url(r'^admin/board/', 'hunt.solving.admin_views.board'),

    url(r'^admin/', include(admin.site.urls)),

)
