from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$', ProgramDayView.as_view(), name='day'),
    url(r'^$', ProgramOverviewView.as_view(), name='index'),
]
