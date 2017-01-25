from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.NewsIndex.as_view(), kwargs={'archived': False}, name='index'),
    url(r'^archive/$', views.NewsIndex.as_view(), kwargs={'archived': True}, name='archive'),
    url(r'(?P<slug>[-_\w+]+)/$', views.NewsDetail.as_view(), name='detail'),
]

