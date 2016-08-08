from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})/$', views.ProgramDayView.as_view(), name='day'),
    url(r'^$', views.ProgramOverviewView.as_view(), name='index'),
    url(r'^speakers/$', views.SpeakerListView.as_view(), name='speaker_index'),
    url(r'speakers/(?P<slug>[-_\w+]+)/$', views.SpeakerDetailView.as_view(), name='speaker_detail'),
    url(r'^events/$', views.EventListView.as_view(), name='event_index'),
    url(r'^(?P<slug>[-_\w+]+)/$', views.EventDetailView.as_view(), name='event'),
]
