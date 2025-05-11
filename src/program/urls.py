from __future__ import annotations

from django.urls import include
from django.urls import path

from .views import CallForParticipationView
from .views import CombinedProposalPersonSelectView
from .views import CombinedProposalSubmitView
from .views import CombinedProposalTypeSelectView
from .views import EventDetailView
from .views import EventListView
from .views import EventProposalAddPersonView
from .views import EventProposalCreateView
from .views import EventProposalDeleteView
from .views import EventProposalDetailView
from .views import EventProposalRemovePersonView
from .views import EventProposalSelectPersonView
from .views import EventProposalTypeSelectView
from .views import EventProposalUpdateView
from .views import FeedbackCreateView
from .views import FeedbackDeleteView
from .views import FeedbackDetailView
from .views import FeedbackListView
from .views import FeedbackRedirectView
from .views import FeedbackUpdateView
from .views import FrabXmlView
from .views import ICSView
from .views import ProgramControlCenter
from .views import ProposalListView
from .views import ScheduleView
from .views import SpeakerDetailView
from .views import SpeakerListView
from .views import SpeakerProposalCreateView
from .views import SpeakerProposalDeleteView
from .views import SpeakerProposalDetailView
from .views import SpeakerProposalUpdateView
from .views import UrlCreateView
from .views import UrlDeleteView
from .views import UrlUpdateView

app_name = "program"

urlpatterns = [
    path("", ScheduleView.as_view(), name="schedule_index"),
    path("noscript/", ScheduleView.as_view(), name="noscript_schedule_index"),
    path("ics/", ICSView.as_view(), name="ics_view"),
    path("frab.xml", FrabXmlView.as_view(), name="frab_view"),
    path("control/", ProgramControlCenter.as_view(), name="program_control_center"),
    # SpeakerProposals and EventProposals
    path(
        "proposals/",
        include(
            [
                path("", ProposalListView.as_view(), name="proposal_list"),
                path(
                    "submit/",
                    include(
                        [
                            path(
                                "",
                                CombinedProposalTypeSelectView.as_view(),
                                name="proposal_combined_type_select",
                            ),
                            path(
                                "<slug:event_type_slug>/",
                                CombinedProposalSubmitView.as_view(),
                                name="proposal_combined_submit",
                            ),
                            path(
                                "<slug:event_type_slug>/select_person/",
                                CombinedProposalPersonSelectView.as_view(),
                                name="proposal_combined_person_select",
                            ),
                        ],
                    ),
                ),
                path(
                    "people/",
                    include(
                        [
                            path(
                                "<uuid:pk>/",
                                SpeakerProposalDetailView.as_view(),
                                name="speaker_proposal_detail",
                            ),
                            path(
                                "<uuid:pk>/update/",
                                SpeakerProposalUpdateView.as_view(),
                                name="speaker_proposal_update",
                            ),
                            path(
                                "<uuid:pk>/delete/",
                                SpeakerProposalDeleteView.as_view(),
                                name="speaker_proposal_delete",
                            ),
                            path(
                                "<uuid:speaker_uuid>/add_event/",
                                EventProposalTypeSelectView.as_view(),
                                name="event_proposal_type_select",
                            ),
                            path(
                                "<uuid:speaker_uuid>/add_event/<slug:event_type_slug>/",
                                EventProposalCreateView.as_view(),
                                name="event_proposal_create",
                            ),
                            path(
                                "<uuid:speaker_uuid>/add_url/",
                                UrlCreateView.as_view(),
                                name="speaker_proposal_url_create",
                            ),
                            path(
                                "<uuid:speaker_uuid>/urls/<uuid:url_uuid>/update/",
                                UrlUpdateView.as_view(),
                                name="speaker_proposal_url_update",
                            ),
                            path(
                                "<uuid:speaker_uuid>/urls/<uuid:url_uuid>/delete/",
                                UrlDeleteView.as_view(),
                                name="speaker_proposal_url_delete",
                            ),
                        ],
                    ),
                ),
                path(
                    "events/",
                    include(
                        [
                            path(
                                "<uuid:pk>/",
                                EventProposalDetailView.as_view(),
                                name="event_proposal_detail",
                            ),
                            path(
                                "<uuid:pk>/update/",
                                EventProposalUpdateView.as_view(),
                                name="event_proposal_update",
                            ),
                            path(
                                "<uuid:pk>/delete/",
                                EventProposalDeleteView.as_view(),
                                name="event_proposal_delete",
                            ),
                            path(
                                "<uuid:event_uuid>/add_person/",
                                EventProposalSelectPersonView.as_view(),
                                name="event_proposal_select_person",
                            ),
                            path(
                                "<uuid:event_uuid>/add_person/new/",
                                SpeakerProposalCreateView.as_view(),
                                name="speaker_proposal_create",
                            ),
                            path(
                                "<uuid:event_uuid>/add_person/<uuid:speaker_uuid>/",
                                EventProposalAddPersonView.as_view(),
                                name="event_proposal_add_person",
                            ),
                            path(
                                "<uuid:event_uuid>/remove_person/<uuid:speaker_uuid>/",
                                EventProposalRemovePersonView.as_view(),
                                name="event_proposal_remove_person",
                            ),
                            # event url views
                            path(
                                "<uuid:event_uuid>/add_url/",
                                UrlCreateView.as_view(),
                                name="event_proposal_url_create",
                            ),
                            path(
                                "<uuid:event_uuid>/urls/<uuid:url_uuid>/update/",
                                UrlUpdateView.as_view(),
                                name="event_proposal_url_update",
                            ),
                            path(
                                "<uuid:event_uuid>/urls/<uuid:url_uuid>/delete/",
                                UrlDeleteView.as_view(),
                                name="event_proposal_url_delete",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    # Speaker views
    path(
        "speakers/",
        include(
            [
                path("", SpeakerListView.as_view(), name="speaker_index"),
                path(
                    "<slug:slug>/",
                    SpeakerDetailView.as_view(),
                    name="speaker_detail",
                ),
            ],
        ),
    ),
    path("events/", EventListView.as_view(), name="event_index"),
    # legacy CFS url kept on purpose to keep old links functional
    path(
        "call-for-speakers/",
        CallForParticipationView.as_view(),
        name="call_for_speakers",
    ),
    path(
        "call-for-participation/",
        CallForParticipationView.as_view(),
        name="call_for_participation",
    ),
    path("calendar", ICSView.as_view(), name="ics_calendar"),
    # this must be the last URL here or the slug will overrule the others
    path(
        "<slug:event_slug>/",
        include(
            [
                path("", EventDetailView.as_view(), name="event_detail"),
                path(
                    "feedback/",
                    include(
                        [
                            path(
                                "",
                                FeedbackRedirectView.as_view(),
                                name="event_feedback_redirect",
                            ),
                            path(
                                "list/",
                                FeedbackListView.as_view(),
                                name="event_feedback_list",
                            ),
                            path(
                                "show/",
                                FeedbackDetailView.as_view(),
                                name="event_feedback_detail",
                            ),
                            path(
                                "create/",
                                FeedbackCreateView.as_view(),
                                name="event_feedback_create",
                            ),
                            path(
                                "update/",
                                FeedbackUpdateView.as_view(),
                                name="event_feedback_update",
                            ),
                            path(
                                "delete/",
                                FeedbackDeleteView.as_view(),
                                name="event_feedback_delete",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
]
