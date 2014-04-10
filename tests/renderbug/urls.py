from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tests.views.home', name='home'),
    url(r'^$', 'renderbug.views.index', name='index'),
    url(r'^print/(.+)$', 'renderbug.views.print_node_tree', name='print-node-tree'),
    url(r'^(.+)$', 'renderbug.views.render_template', name='render-template'),
)
