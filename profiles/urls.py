from django.conf.urls import url

from .views import ProfileDetail

urlpatterns = [
    url(r'^$', ProfileDetail.as_view(), name='detail'),
]