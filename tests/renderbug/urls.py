from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tests.views.home', name='home'),
    url(r'^$', 'renderbug.views.index', name='index'),
    url(r'^(.+)$', 'renderbug.views.render_template', name='render-template'),
)
