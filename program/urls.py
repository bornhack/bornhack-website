from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^$', ProgramView.as_view(), name='index')
]
