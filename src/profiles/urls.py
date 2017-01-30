from django.conf.urls import url

from .views import ProfileDetail, ProfileUpdate

urlpatterns = [
    url(r'^$', ProfileDetail.as_view(), name='detail'),
    url(r'^edit$', ProfileUpdate.as_view(), name='update'),
]
