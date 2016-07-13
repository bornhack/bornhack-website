from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^$', ProgramIndexView.as_view(), name='index')
]
