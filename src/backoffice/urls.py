from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^$', BackofficeIndexView.as_view(), name='index'),
    url(r'infodesk/$', InfodeskView.as_view(), name='infodesk_index'),
]

