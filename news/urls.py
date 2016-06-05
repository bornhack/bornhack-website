from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.NewsIndex.as_view(), name='index'),
    url(r'(?P<slug>[-_\w+]+)/$', views.NewsDetail.as_view(), name='detail'),
]
