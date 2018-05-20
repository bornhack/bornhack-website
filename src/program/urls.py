from django.conf.urls import include, url
from .views import *

app_name = 'program'

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
        r'^proposals/', include([
            url(
                r'^$',
                ProposalListView.as_view(),
                name='proposal_list',
            ),
            url(
                r'^submit/', include([
                    url(
                        r'^$',
                        CombinedProposalTypeSelectView.as_view(),
                        name='proposal_combined_type_select',
                    ),
                    url(
                        r'^(?P<event_type_slug>[-_\w+]+)/$',
                        CombinedProposalSubmitView.as_view(),
                        name='proposal_combined_submit',
                    ),
                ]),
            ),
            url(
                r'^people/', include([
                    url(
                        r'^(?P<pk>[a-f0-9-]+)/update/$',
                        SpeakerProposalUpdateView.as_view(),
                        name='speakerproposal_update'
                    ),
                    url(
                        r'^(?P<pk>[a-f0-9-]+)/delete/$',
                        SpeakerProposalDeleteView.as_view(),
                        name='speakerproposal_delete'
                    ),
                    url(
                        r'^(?P<speaker_uuid>[a-f0-9-]+)/add_event/$',
                        EventProposalTypeSelectView.as_view(),
                        name='eventproposal_typeselect'
                    ),
                    url(
                        r'^(?P<speaker_uuid>[a-f0-9-]+)/add_event/(?P<event_type_slug>[-_\w+]+)/$',
                        EventProposalCreateView.as_view(),
                        name='eventproposal_create'
                    ),
                ])
            ),
            url(
                r'^events/', include([
                    url(
                        r'^(?P<pk>[a-f0-9-]+)/edit/$',
                        EventProposalUpdateView.as_view(),
                        name='eventproposal_update'
                    ),
                    url(
                        r'^(?P<pk>[a-f0-9-]+)/delete/$',
                        EventProposalDeleteView.as_view(),
                        name='eventproposal_delete'
                    ),
                    url(
                        r'^(?P<event_uuid>[a-f0-9-]+)/add_person/$',
                        EventProposalSelectPersonView.as_view(),
                        name='eventproposal_selectperson'
                    ),
                    url(
                        r'^(?P<event_uuid>[a-f0-9-]+)/add_person/new/$',
                        SpeakerProposalCreateView.as_view(),
                        name='speakerproposal_create'
                    ),
                    url(
                        r'^(?P<event_uuid>[a-f0-9-]+)/add_person/(?P<speaker_uuid>[a-f0-9-]+)/$',
                        EventProposalAddPersonView.as_view(),
                        name='eventproposal_addperson'
                    ),
                ])
            ),
        ])
    ),
    url(
        r'^speakers/', include([
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
        ]),
    ),
    url(
        r'^events/$',
        EventListView.as_view(),
        name='event_index'
    ),
    # legacy CFS url kept on purpose to keep old links functional
    url(
        r'^call-for-speakers/$',
        CallForParticipationView.as_view(),
        name='call_for_speakers'
    ),
    url(
        r'^call-for-participation/$',
        CallForParticipationView.as_view(),
        name='call_for_participation'
    ),
    url(
        r'^calendar/',
        ICSView.as_view(),
        name='ics_calendar'
    ),
    # this must be the last URL here or the regex will overrule the others
    url(
        r'^(?P<slug>[-_\w+]+)/$',
        EventDetailView.as_view(),
        name='event_detail'
    ),
]

