from django.urls import include, path

from .views import (
    ApproveFeedbackView,
    ApproveNamesView,
    AutoScheduleApplyView,
    AutoScheduleCalculateView,
    AutoScheduleCreateObjectsView,
    AutoScheduleCreateView,
    AutoScheduleDebugEventsView,
    AutoScheduleDebugSlotsView,
    AutoScheduleDeleteView,
    AutoScheduleDetailView,
    AutoScheduleDiffView,
    AutoScheduleListView,
    BackofficeIndexView,
    BadgeHandoutView,
    ChainDetailView,
    ChainListView,
    CredebtorDetailView,
    EventProposalManageView,
    EventSessionCreateLocationSelectView,
    EventSessionCreateTypeSelectView,
    EventSessionCreateView,
    EventSessionDeleteView,
    EventSessionDetailView,
    EventSessionListView,
    EventSessionUpdateView,
    ExpenseDetailView,
    ExpenseListView,
    FacilityFeedbackView,
    ManageProposalsView,
    MerchandiseOrdersView,
    MerchandiseToOrderView,
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
    SpeakerProposalManageView,
    TicketCheckinView,
    VillageOrdersView,
    VillageToOrderView,
)

app_name = "backoffice"

urlpatterns = [
    path("", BackofficeIndexView.as_view(), name="index"),
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
    # manage proposals
    path(
        "manage_proposals/",
        include(
            [
                path("", ManageProposalsView.as_view(), name="manage_proposals"),
                path(
                    "speakers/<uuid:pk>/",
                    SpeakerProposalManageView.as_view(),
                    name="speakerproposal_manage",
                ),
                path(
                    "events/<uuid:pk>/",
                    EventProposalManageView.as_view(),
                    name="eventproposal_manage",
                ),
            ]
        ),
    ),
    # manage eventsession objects
    path(
        "eventsessions/",
        include(
            [
                path("", EventSessionListView.as_view(), name="eventsession_list"),
                path(
                    "create/",
                    include(
                        [
                            path(
                                "",
                                EventSessionCreateTypeSelectView.as_view(),
                                name="eventsession_typeselect",
                            ),
                            path(
                                "<slug:eventtype_slug>/",
                                include(
                                    [
                                        path(
                                            "",
                                            EventSessionCreateLocationSelectView.as_view(),
                                            name="eventsession_locationselect",
                                        ),
                                        path(
                                            "<slug:eventlocation_slug>/",
                                            EventSessionCreateView.as_view(),
                                            name="eventsession_create",
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
                                name="eventsession_detail",
                            ),
                            path(
                                "update/",
                                EventSessionUpdateView.as_view(),
                                name="eventsession_update",
                            ),
                            path(
                                "delete/",
                                EventSessionDeleteView.as_view(),
                                name="eventsession_delete",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # manage autoschedule objects
    path(
        "autoscheduler/",
        include(
            [
                path("", AutoScheduleListView.as_view(), name="autoschedule_list"),
                path(
                    "create/",
                    AutoScheduleCreateView.as_view(),
                    name="autoschedule_create",
                ),
                path(
                    "<int:pk>/",
                    include(
                        [
                            path(
                                "",
                                AutoScheduleDetailView.as_view(),
                                name="autoschedule_detail",
                            ),
                            path(
                                "create_objects/",
                                AutoScheduleCreateObjectsView.as_view(),
                                name="autoschedule_create_objects",
                            ),
                            path(
                                "calculate/",
                                AutoScheduleCalculateView.as_view(),
                                name="autoschedule_calculate",
                            ),
                            path(
                                "diff/",
                                AutoScheduleDiffView.as_view(),
                                name="autoschedule_diff",
                            ),
                            path(
                                "diff/<int:original_schedule_id>/",
                                AutoScheduleDiffView.as_view(),
                                name="autoschedule_diff",
                            ),
                            path(
                                "debug-slots/",
                                AutoScheduleDebugSlotsView.as_view(),
                                name="autoschedule_debug_slots",
                            ),
                            path(
                                "debug-events/",
                                AutoScheduleDebugEventsView.as_view(),
                                name="autoschedule_debug_events",
                            ),
                            path(
                                "apply/",
                                AutoScheduleApplyView.as_view(),
                                name="autoschedule_apply",
                            ),
                            path(
                                "delete/",
                                AutoScheduleDeleteView.as_view(),
                                name="autoschedule_delete",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # approve eventfeedback objects
    path(
        "approve_feedback", ApproveFeedbackView.as_view(), name="approve_eventfeedback",
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
