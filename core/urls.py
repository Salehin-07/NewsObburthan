from django.urls import path, register_converter
from . import views

class UnicodeSluConverter:
    regex = r'[\w\u0980-\u09FF][\w\u0980-\u09FF\-]*'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
        
        
register_converter(UnicodeSluConverter, 'uslug')




app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('tag/<uslug:tag>/', views.tag_feed, name='tag_feed'),
    path('posts/details/<uslug:slug>/', views.post_detail, name='post_detail'),
    path('contact/',  views.ContactView.as_view(), name='contact'),
    path('portal/',    views.PortalView.as_view(),  name='portal'),
]
