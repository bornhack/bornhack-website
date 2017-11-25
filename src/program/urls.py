from django.conf.urls import url, include

from program.views import (
    ScheduleView,
    NoScriptScheduleView,
    ICSView,
    ProgramControlCenter,
    ProposalListView,
    SpeakerProposalCreateView,
    SpeakerProposalDetailView, SpeakerProposalUpdateView, SpeakerProposalSubmitView, SpeakerProposalPictureView,
    EventProposalCreateView, EventProposalDetailView, EventProposalUpdateView, EventProposalSubmitView, SpeakerListView,
    SpeakerDetailView, SpeakerPictureView, EventListView, CallForSpeakersView, EventDetailView)

speaker_proposal_urls = [
    url(
        r'^create/$',
        SpeakerProposalCreateView.as_view(),
        name='speakerproposal_create'
    ),
    url(
        r'^(?P<pk>[a-f0-9-]+)/$',
        SpeakerProposalDetailView.as_view(),
        name='speakerproposal_detail'
    ),
    url(
        r'^(?P<pk>[a-f0-9-]+)/edit/$',
        SpeakerProposalUpdateView.as_view(),
        name='speakerproposal_update'
    ),
    url(
        r'^(?P<pk>[a-f0-9-]+)/submit/$',
        SpeakerProposalSubmitView.as_view(),
        name='speakerproposal_submit'
    ),
    url(
        r'^(?P<pk>[a-f0-9-]+)/picture/$',
        SpeakerProposalPictureView.as_view(),
        name='speakerproposal_picture',
    ),
]

event_proposal_urls = [
    url(
        r'^create/$',
        EventProposalCreateView.as_view(),
        name='eventproposal_create'
    ),
    url(
        r'^(?P<pk>[a-f0-9-]+)/$',
        EventProposalDetailView.as_view(),
        name='eventproposal_detail'
    ),
    url(
        r'^(?P<pk>[a-f0-9-]+)/edit/$',
        EventProposalUpdateView.as_view(),
        name='eventproposal_update'
    ),
    url(
        r'^(?P<pk>[a-f0-9-]+)/submit/$',
        EventProposalSubmitView.as_view(),
        name='eventproposal_submit'
    ),
]

proposal_urls = [
    url(
        r'^$',
        ProposalListView.as_view(),
        name='proposal_list',
    ),
    url(
        r'^speakers/', include(speaker_proposal_urls)
    ),
    url(
        r'^events/', include(event_proposal_urls)
    ),
]

speaker_urls = [
    url(
        r'^$',
        SpeakerListView.as_view(),
        name='speaker_index'
    ),
    url(
        r'^(?P<slug>[-_\w+]+)/$',
        SpeakerDetailView.as_view(),
        name='speaker_detail'
    ),
    url(
        r'^(?P<slug>[-_\w+]+)/pictures/(?P<picture>[-_\w+]+)/$',
        SpeakerPictureView.as_view(),
        name='speaker_picture',
    ),
]

urlpatterns = [
    url(
        r'^$',
        ScheduleView.as_view(),
        name='schedule_index'
    ),
    url(
        r'^noscript/$',
        NoScriptScheduleView.as_view(),
        name='noscript_schedule_index'
    ),
    url(
        r'^ics/', ICSView.as_view(), name="ics_view"
    ),
    url(
        r'^control/', ProgramControlCenter.as_view(), name="program_control_center"
    ),
    url(
        r'^proposals/', include(proposal_urls)
    ),
    url(
        r'^speakers/', include(speaker_urls),
    ),
    url(
        r'^events/$',
        EventListView.as_view(),
        name='event_index'
    ),
    url(
        r'^call-for-speakers/$',
        CallForSpeakersView.as_view(),
        name='call_for_speakers'
    ),
    url(
        r'^calendar/',
        ICSView.as_view(),
        name='ics_calendar'
    ),
    # this has to be the last URL here
    url(
        r'^(?P<slug>[-_\w+]+)/$',
        EventDetailView.as_view(),
        name='event_detail'
    ),
]