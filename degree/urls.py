from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('degree.views',
	url(r'^test/$', 'test', name = 'test'),
    url(r'^$', 'home', name = 'home'),
    url(r'^register/$', 'register', name='register'),
    url(r'^confirm-email/(?P<username>[\w.@+-]+)/(?P<token>\d+)/$',
        'confirm_email', name='confirm email'),
    
    # TODO: To be renamed
    url(r'^create-degree/$', 'create_degree', name='create degree'),
    url(r'^create-degree/new_school/$', 'create_new_school', name="create school"),
    url(r'^create-degree/existing_school/$', 'create_existing_school', name="existing school"),
    url(r'^create-degree/(?P<school>[^/]+)/get_public$','get_public', name='get public'),
    url(r'^create/(?P<school>[^/]+)/(?P<program>[^/]+)/$','create', name='create'),
    url(r'^create/(?P<school>[^/]+)/(?P<program>[^/]+)/group$', 'create_group', name='create group'),
    url(r'^create/(?P<school>[^/]+)/(?P<program>[^/]+)/class$', 'create_class', name='create class'),
    url(r'^create/(?P<school>[^/]+)/(?P<program>[^/]+)/category$', 'create_category', name='create category'),
    url(r'^create/(?P<school>[^/]+)/(?P<program>[^/]+)/faculty$', 'create_faculty', name='create faculty'),
    url(r'^create/(?P<school>[^/]+)/(?P<program>[^/]+)/remove_group_(?P<group_id>\d+)$', 'remove_group', name='remove group'),
    url(r'^create/(?P<school>[^/]+)/(?P<program>[^/]+)/remove_category_(?P<category_id>\d+)$', 'remove_category', name='remove category'),
    url(r'^create/(?P<school>[^/]+)/(?P<program>[^/]+)/assign_categories', 'assign_categories', name='assign categories'),
    url(r'^create/(?P<school>[^/]+)/(?P<program>[^/]+)/finalize', 'finalize_program', name='finalize program'),


    url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/$','build', name='build'),
    url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/(?P<category_id>[\d]+)$','build', name='build category'),
    url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/(?P<category_id>[\d]+)/add_class_(?P<class_id>[\d]+)$','add_class', name='add class'),
   	url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/(?P<category_id>[\d]+)/remove_class_(?P<class_id>[\d]+)$','remove_class', name='remove class'),
   	url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/(?P<category_id>[\d]+)/add_grade_(?P<class_id>[\d]+)$','add_grade', name='add grade'),
   	url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/(?P<category_id>[\d]+)/generate_details_(?P<category_id2>[\d]+)$','generate_details', name='generate details'),
	url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/analyze$','analyze_program', name='analyze'),
	url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/publish$','publish', name='publish'),
	url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/info$','program_info', name='program info'),
	url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/gradesheet$','gradesheet', name='gradesheet'),
    url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/regenerate_link$','regenerate_link', name='regenerate'),
	url(r'^gradesheet/(?P<identifier>[\w]+)$','gradesheet_public', name='gradesheet public'),
    url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/(?P<category_id>[\d]+)/add_all$','add_all', name='add all'),
    url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/(?P<category_id>[\d]+)/add_from_public$','add_from_public', name='add from public'),
    url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/add_from_public_no_cat$','add_from_public_no_cat', name='add from public nocat'),
    url(r'^build/(?P<school>[^/]+)/(?P<program>[^/]+)/(?P<category_id>[\d]+)/remove_all$','remove_all', name='remove all'),

)


urlpatterns += patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', name = 'login'),
    url(r'^logout/$', 'logout_then_login', name = 'logout'),
)