from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<slug>[-_\w+]+)/$', views.EventDetailView.as_view(), name='event'),
    url(r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$', views.ProgramDayView.as_view(), name='day'),
    url(r'^$', views.ProgramOverviewView.as_view(), name='index'),
]
