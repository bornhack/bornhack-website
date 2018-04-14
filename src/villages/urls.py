from django.conf.urls import url
from .views import *


app_name = 'villages'

urlpatterns = [
    url(r'^$', VillageListView.as_view(), name='list'),
    url(r'create/$', VillageCreateView.as_view(), name='create'),
    url(r'(?P<slug>[-_\w+]+)/delete/$', VillageDeleteView.as_view(), name='delete'),
    url(r'(?P<slug>[-_\w+]+)/edit/$', VillageUpdateView.as_view(), name='update'),
    url(r'(?P<slug>[-_\w+]+)/$', VillageDetailView.as_view(), name='detail'),
]
