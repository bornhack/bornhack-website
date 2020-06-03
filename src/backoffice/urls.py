from django.urls import include, path

from .views import (
    ApproveFeedbackView,
    ApproveNamesView,
    AutoScheduleApplyView,
    AutoScheduleCrashCourseView,
    AutoScheduleDebugEventConflictsView,
    AutoScheduleDebugEventSlotUnavailabilityView,
    AutoScheduleDiffView,
    AutoScheduleManageView,
    AutoScheduleValidateView,
    BackofficeIndexView,
    BackofficeProxyView,
    BadgeHandoutView,
    ChainDetailView,
    ChainListView,
    CredebtorDetailView,
    EventDeleteView,
    EventDetailView,
    EventListView,
    EventLocationCreateView,
    EventLocationDeleteView,
    EventLocationDetailView,
    EventLocationListView,
    EventLocationUpdateView,
    EventProposalApproveRejectView,
    EventProposalDetailView,
    EventProposalListView,
    EventScheduleView,
    EventSessionCreateLocationSelectView,
    EventSessionCreateTypeSelectView,
    EventSessionCreateView,
    EventSessionDeleteView,
    EventSessionDetailView,
    EventSessionListView,
    EventSessionUpdateView,
    EventSlotDetailView,
    EventSlotListView,
    EventSlotUnscheduleView,
    EventTypeDetailView,
    EventTypeListView,
    EventUpdateView,
    ExpenseDetailView,
    ExpenseListView,
    FacilityFeedbackView,
    MerchandiseOrdersView,
    MerchandiseToOrderView,
    PendingProposalsView,
    ProductHandoutView,
    ReimbursementCreateUserSelectView,
    ReimbursementCreateView,
    ReimbursementDeleteView,
    ReimbursementDetailView,
    ReimbursementListView,
    ReimbursementUpdateView,
    RevenueDetailView,
    RevenueListView,
    ScanTicketsView,
    ShopTicketOverview,
    SpeakerDeleteView,
    SpeakerDetailView,
    SpeakerListView,
    SpeakerProposalApproveRejectView,
    SpeakerProposalDetailView,
    SpeakerProposalListView,
    SpeakerUpdateView,
    TicketCheckinView,
    VillageOrdersView,
    VillageToOrderView,
)

app_name = "backoffice"

urlpatterns = [
    path("", BackofficeIndexView.as_view(), name="index"),
    # proxy view
    path("proxy/", BackofficeProxyView.as_view(), name="proxy"),
    path("proxy/<slug:proxy_slug>/", BackofficeProxyView.as_view(), name="proxy"),
    # facility feedback
    path(
        "feedback/facilities/<slug:team_slug>/",
        include([path("", FacilityFeedbackView.as_view(), name="facilityfeedback")]),
    ),
    # infodesk
    path(
        "infodesk/",
        include([path("", ScanTicketsView.as_view(), name="scan_tickets")]),
    ),
    path("shop_tickets/", ShopTicketOverview.as_view(), name="shop_ticket_overview"),
    path("product_handout/", ProductHandoutView.as_view(), name="product_handout"),
    path("badge_handout/", BadgeHandoutView.as_view(), name="badge_handout"),
    path("ticket_checkin/", TicketCheckinView.as_view(), name="ticket_checkin"),
    # public names
    path(
        "public_credit_names/", ApproveNamesView.as_view(), name="public_credit_names"
    ),
    # merchandise orders
    path(
        "merchandise_orders/",
        MerchandiseOrdersView.as_view(),
        name="merchandise_orders",
    ),
    path(
        "merchandise_to_order/",
        MerchandiseToOrderView.as_view(),
        name="merchandise_to_order",
    ),
    # village orders
    path("village_orders/", VillageOrdersView.as_view(), name="village_orders"),
    path("village_to_order/", VillageToOrderView.as_view(), name="village_to_order"),
    # manage SpeakerProposals and EventProposals
    path(
        "proposals/",
        include(
            [
                path(
                    "pending/", PendingProposalsView.as_view(), name="pending_proposals"
                ),
                path(
                    "speakers/",
                    include(
                        [
                            path(
                                "",
                                SpeakerProposalListView.as_view(),
                                name="speaker_proposal_list",
                            ),
                            path(
                                "<uuid:pk>/",
                                include(
                                    [
                                        path(
                                            "",
                                            SpeakerProposalDetailView.as_view(),
                                            name="speaker_proposal_detail",
                                        ),
                                        path(
                                            "approve_reject/",
                                            SpeakerProposalApproveRejectView.as_view(),
                                            name="speaker_proposal_approve_reject",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                path(
                    "events/",
                    include(
                        [
                            path(
                                "",
                                EventProposalListView.as_view(),
                                name="event_proposal_list",
                            ),
                            path(
                                "<uuid:pk>/",
                                include(
                                    [
                                        path(
                                            "",
                                            EventProposalDetailView.as_view(),
                                            name="event_proposal_detail",
                                        ),
                                        path(
                                            "approve_reject/",
                                            EventProposalApproveRejectView.as_view(),
                                            name="event_proposal_approve_reject",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # manage EventSession objects
    path(
        "event_sessions/",
        include(
            [
                path("", EventSessionListView.as_view(), name="event_session_list"),
                path(
                    "create/",
                    include(
                        [
                            path(
                                "",
                                EventSessionCreateTypeSelectView.as_view(),
                                name="event_session_create_type_select",
                            ),
                            path(
                                "<slug:event_type_slug>/",
                                include(
                                    [
                                        path(
                                            "",
                                            EventSessionCreateLocationSelectView.as_view(),
                                            name="event_session_create_location_select",
                                        ),
                                        path(
                                            "<slug:event_location_slug>/",
                                            EventSessionCreateView.as_view(),
                                            name="event_session_create",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                path(
                    "<int:pk>/",
                    include(
                        [
                            path(
                                "",
                                EventSessionDetailView.as_view(),
                                name="event_session_detail",
                            ),
                            path(
                                "update/",
                                EventSessionUpdateView.as_view(),
                                name="event_session_update",
                            ),
                            path(
                                "delete/",
                                EventSessionDeleteView.as_view(),
                                name="event_session_delete",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # manage EventSlot objects
    path(
        "event_slots/",
        include(
            [
                path("", EventSlotListView.as_view(), name="event_slot_list"),
                path(
                    "<int:pk>/",
                    include(
                        [
                            path(
                                "",
                                EventSlotDetailView.as_view(),
                                name="event_slot_detail",
                            ),
                            path(
                                "unschedule/",
                                EventSlotUnscheduleView.as_view(),
                                name="event_slot_unschedule",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # manage Speaker objects
    path(
        "speakers/",
        include(
            [
                path("", SpeakerListView.as_view(), name="speaker_list"),
                path(
                    "<slug:slug>/",
                    include(
                        [
                            path(
                                "", SpeakerDetailView.as_view(), name="speaker_detail",
                            ),
                            path(
                                "update/",
                                SpeakerUpdateView.as_view(),
                                name="speaker_update",
                            ),
                            path(
                                "delete/",
                                SpeakerDeleteView.as_view(),
                                name="speaker_delete",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # manage EventType objects
    path(
        "event_types/",
        include(
            [
                path("", EventTypeListView.as_view(), name="event_type_list"),
                path(
                    "<slug:slug>/",
                    EventTypeDetailView.as_view(),
                    name="event_type_detail",
                ),
            ]
        ),
    ),
    # manage EventLocation objects
    path(
        "event_locations/",
        include(
            [
                path("", EventLocationListView.as_view(), name="event_location_list"),
                path(
                    "create/",
                    EventLocationCreateView.as_view(),
                    name="event_location_create",
                ),
                path(
                    "<slug:slug>/",
                    include(
                        [
                            path(
                                "",
                                EventLocationDetailView.as_view(),
                                name="event_location_detail",
                            ),
                            path(
                                "update/",
                                EventLocationUpdateView.as_view(),
                                name="event_location_update",
                            ),
                            path(
                                "delete/",
                                EventLocationDeleteView.as_view(),
                                name="event_location_delete",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # manage Event objects
    path(
        "events/",
        include(
            [
                path("", EventListView.as_view(), name="event_list"),
                path(
                    "<slug:slug>/",
                    include(
                        [
                            path("", EventDetailView.as_view(), name="event_detail",),
                            path(
                                "update/",
                                EventUpdateView.as_view(),
                                name="event_update",
                            ),
                            path(
                                "schedule/",
                                EventScheduleView.as_view(),
                                name="event_schedule",
                            ),
                            path(
                                "delete/",
                                EventDeleteView.as_view(),
                                name="event_delete",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # manage AutoScheduler
    path(
        "autoscheduler/",
        include(
            [
                path("", AutoScheduleManageView.as_view(), name="autoschedule_manage",),
                path(
                    "crashcourse/",
                    AutoScheduleCrashCourseView.as_view(),
                    name="autoschedule_crash_course",
                ),
                path(
                    "validate/",
                    AutoScheduleValidateView.as_view(),
                    name="autoschedule_validate",
                ),
                path(
                    "diff/", AutoScheduleDiffView.as_view(), name="autoschedule_diff",
                ),
                path(
                    "apply/",
                    AutoScheduleApplyView.as_view(),
                    name="autoschedule_apply",
                ),
                path(
                    "debug-event-slot-unavailability/",
                    AutoScheduleDebugEventSlotUnavailabilityView.as_view(),
                    name="autoschedule_debug_event_slot_unavailability",
                ),
                path(
                    "debug-event-conflicts/",
                    AutoScheduleDebugEventConflictsView.as_view(),
                    name="autoschedule_debug_event_conflicts",
                ),
            ]
        ),
    ),
    # approve EventFeedback objects
    path(
        "approve_feedback",
        ApproveFeedbackView.as_view(),
        name="approve_event_feedback",
    ),
    # economy
    path(
        "economy/",
        include(
            [
                # chains & credebtors
                path(
                    "chains/",
                    include(
                        [
                            path("", ChainListView.as_view(), name="chain_list"),
                            path(
                                "<slug:chain_slug>/",
                                include(
                                    [
                                        path(
                                            "",
                                            ChainDetailView.as_view(),
                                            name="chain_detail",
                                        ),
                                        path(
                                            "<slug:credebtor_slug>/",
                                            CredebtorDetailView.as_view(),
                                            name="credebtor_detail",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                # expenses
                path(
                    "expenses/",
                    include(
                        [
                            path("", ExpenseListView.as_view(), name="expense_list"),
                            path(
                                "<uuid:pk>/",
                                ExpenseDetailView.as_view(),
                                name="expense_detail",
                            ),
                        ]
                    ),
                ),
                # revenues
                path(
                    "revenues/",
                    include(
                        [
                            path("", RevenueListView.as_view(), name="revenue_list"),
                            path(
                                "<uuid:pk>/",
                                RevenueDetailView.as_view(),
                                name="revenue_detail",
                            ),
                        ]
                    ),
                ),
                # reimbursements
                path(
                    "reimbursements/",
                    include(
                        [
                            path(
                                "",
                                ReimbursementListView.as_view(),
                                name="reimbursement_list",
                            ),
                            path(
                                "<uuid:pk>/",
                                include(
                                    [
                                        path(
                                            "",
                                            ReimbursementDetailView.as_view(),
                                            name="reimbursement_detail",
                                        ),
                                        path(
                                            "update/",
                                            ReimbursementUpdateView.as_view(),
                                            name="reimbursement_update",
                                        ),
                                        path(
                                            "delete/",
                                            ReimbursementDeleteView.as_view(),
                                            name="reimbursement_delete",
                                        ),
                                    ]
                                ),
                            ),
                            path(
                                "create/",
                                ReimbursementCreateUserSelectView.as_view(),
                                name="reimbursement_create_userselect",
                            ),
                            path(
                                "create/<int:user_id>/",
                                ReimbursementCreateView.as_view(),
                                name="reimbursement_create",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
