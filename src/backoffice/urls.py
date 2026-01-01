from __future__ import annotations

from django.urls import include
from django.urls import path

from .views import AccountingExportCreateView
from .views import AccountingExportDeleteView
from .views import AccountingExportDetailView
from .views import AccountingExportDownloadArchiveView
from .views import AccountingExportDownloadFileView
from .views import AccountingExportListView
from .views import AccountingExportUpdateView
from .views import AddRecordingView
from .views import ApproveFeedbackView
from .views import ApproveNamesView
from .views import AutoScheduleApplyView
from .views import AutoScheduleCrashCourseView
from .views import AutoScheduleDebugEventConflictsView
from .views import AutoScheduleDebugEventSlotUnavailabilityView
from .views import AutoScheduleDiffView
from .views import AutoScheduleManageView
from .views import AutoScheduleValidateView
from .views import BackofficeIndexView
from .views import BackofficeProxyView
from .views import BankAccountDetailView
from .views import BankCSVUploadView
from .views import BankDetailView
from .views import BankListView
from .views import BankTransactionDetailView
from .views import ChainDetailView
from .views import ChainListView
from .views import ClearhausSettlementDetailView
from .views import ClearhausSettlementImportView
from .views import ClearhausSettlementListView
from .views import CoinifyBalanceListView
from .views import CoinifyCSVImportView
from .views import CoinifyDashboardView
from .views import CoinifyInvoiceListView
from .views import CoinifyPaymentIntentListView
from .views import CoinifyPayoutListView
from .views import CoinifySettlementListView
from .views import CredebtorDetailView
from .views import CreditNoteDownloadView
from .views import CreditNoteListView
from .views import EpayCSVImportView
from .views import EpayTransactionListView
from .views import EventDeleteView
from .views import EventDetailView
from .views import EventListView
from .views import EventLocationCreateView
from .views import EventLocationDeleteView
from .views import EventLocationDetailView
from .views import EventLocationListView
from .views import EventLocationUpdateView
from .views import EventProposalApproveRejectView
from .views import EventProposalDetailView
from .views import EventProposalListView
from .views import EventScheduleView
from .views import EventSessionCreateLocationSelectView
from .views import EventSessionCreateTypeSelectView
from .views import EventSessionCreateView
from .views import EventSessionDeleteView
from .views import EventSessionDetailView
from .views import EventSessionListView
from .views import EventSessionUpdateView
from .views import EventSlotDetailView
from .views import EventSlotListView
from .views import EventSlotUnscheduleView
from .views import EventTypeDetailView
from .views import EventTypeListView
from .views import EventUpdateView
from .views import ExpenseDetailView
from .views import ExpenseListView
from .views import ExpenseUpdateView
from .views import FacilityCreateView
from .views import FacilityDeleteView
from .views import FacilityDetailView
from .views import FacilityFeedbackView
from .views import FacilityListView
from .views import FacilityOpeningHoursCreateView
from .views import FacilityOpeningHoursDeleteView
from .views import FacilityOpeningHoursUpdateView
from .views import FacilityTypeCreateView
from .views import FacilityTypeDeleteView
from .views import FacilityTypeImportView
from .views import FacilityTypeListView
from .views import FacilityTypeUpdateView
from .views import FacilityUpdateView
from .views import EventFeedbackDetailView
from .views import EventFeedbackListView
from .views import EventFeedbackProcessView
from .views import InvoiceDownloadMultipleView
from .views import InvoiceDownloadView
from .views import InvoiceListCSVView
from .views import InvoiceListView
from .views import IrcOverView
from .views import MapExternalLayerCreateView
from .views import MapExternalLayerDeleteView
from .views import MapExternalLayerUpdateView
from .views import MapFeatureCreateView
from .views import MapFeatureDeleteView
from .views import MapFeatureListView
from .views import MapFeatureUpdateView
from .views import MapLayerCreateView
from .views import MapLayerDeleteView
from .views import MapLayerFeaturesImportView
from .views import MapLayerListView
from .views import MapLayerUpdateView
from .views import MapUserLocationTypeCreateView
from .views import MapUserLocationTypeDeleteView
from .views import MapUserLocationTypeListView
from .views import MapUserLocationTypeUpdateView
from .views import MerchandiseOrdersLabelsView
from .views import MerchandiseOrdersView
from .views import MerchandiseToOrderView
from .views import MobilePayCSVImportView
from .views import MobilePayTransactionListView
from .views import OrderDetailView
from .views import OrderDownloadProformaInvoiceView
from .views import OrderListView
from .views import OrderRefundView
from .views import OrderUpdateView
from .views import OutgoingEmailMassUpdateView
from .views import PendingProposalsView
from .views import PermissionByGroupView
from .views import PermissionByPermissionView
from .views import PermissionByUserView
from .views import PosCreateView
from .views import PosDeleteView
from .views import PosDetailView
from .views import PosListView
from .views import PosProductCostListView
from .views import PosProductCostUpdateView
from .views import PosProductListView
from .views import PosProductUpdateView
from .views import PosReportBankCountEndView
from .views import PosReportBankCountStartView
from .views import PosReportCreateView
from .views import PosReportDetailView
from .views import PosReportListView
from .views import PosReportPosCountEndView
from .views import PosReportPosCountStartView
from .views import PosReportUpdateView
from .views import PosSaleListView
from .views import PosSalesImportView
from .views import PosTransactionListView
from .views import PosUpdateView
from .views import RefundDetailView
from .views import RefundListView
from .views import RefundUpdateView
from .views import ReimbursementDeleteView
from .views import ReimbursementDetailView
from .views import ReimbursementListView
from .views import ReimbursementUpdateView
from .views import RevenueDetailView
from .views import RevenueListView
from .views import RevenueUpdateView
from .views import ScanInventoryIndexView
from .views import ScanInventoryView
from .views import ScanTicketsPosSelectView
from .views import ScanTicketsView
from .views import ShopTicketOverview
from .views import ShopTicketStatsDetailView
from .views import ShopTicketStatsView
from .views import SpeakerDeleteView
from .views import SpeakerDetailView
from .views import SpeakerListView
from .views import SpeakerProposalApproveRejectView
from .views import SpeakerProposalDetailView
from .views import SpeakerProposalListView
from .views import SpeakerUpdateView
from .views import TeamPermissionIndexView
from .views import TeamPermissionManageView
from .views import TokenCategoryCreateView
from .views import TokenCategoryDeleteView
from .views import TokenCategoryDetailView
from .views import TokenCategoryListView
from .views import TokenCategoryUpdateView
from .views import TokenCreateView
from .views import TokenDeleteView
from .views import TokenDetailView
from .views import TokenListView
from .views import TokenStatsView
from .views import TokenUpdateView
from .views import VillageOrdersView
from .views import VillageToOrderView
from .views import ZettleBalanceListView
from .views import ZettleDashboardView
from .views import ZettleDataImportView
from .views import ZettleReceiptListView

app_name = "backoffice"

urlpatterns = [
    path("", BackofficeIndexView.as_view(), name="index"),
    # proxy view
    path("proxy/", BackofficeProxyView.as_view(), name="proxy"),
    path("proxy/<slug:proxy_slug>/", BackofficeProxyView.as_view(), name="proxy"),
    # facilities
    path(
        "feedback/facilities/<slug:team_slug>/",
        include([path("", FacilityFeedbackView.as_view(), name="facilityfeedback")]),
    ),
    path(
        "facility_types/",
        include(
            [
                path("", FacilityTypeListView.as_view(), name="facility_type_list"),
                path(
                    "create/",
                    FacilityTypeCreateView.as_view(),
                    name="facility_type_create",
                ),
                path(
                    "<slug:slug>/",
                    include(
                        [
                            path(
                                "import/",
                                FacilityTypeImportView.as_view(),
                                name="facility_type_import",
                            ),
                            path(
                                "update/",
                                FacilityTypeUpdateView.as_view(),
                                name="facility_type_update",
                            ),
                            path(
                                "delete/",
                                FacilityTypeDeleteView.as_view(),
                                name="facility_type_delete",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "maps/",
        include(
            [
                path("", MapLayerListView.as_view(), name="map_layer_list"),
                path(
                    "create/",
                    MapLayerCreateView.as_view(),
                    name="map_layer_create",
                ),
                path(
                    "user_location_type/",
                    include(
                        [
                            path(
                                "",
                                MapUserLocationTypeListView.as_view(),
                                name="map_user_location_type_list",
                            ),
                            path(
                                "create/",
                                MapUserLocationTypeCreateView.as_view(),
                                name="map_user_location_type_create",
                            ),
                            path(
                                "<uuid:user_location_type_uuid>/",
                                include(
                                    [
                                        path(
                                            "update/",
                                            MapUserLocationTypeUpdateView.as_view(),
                                            name="map_user_location_type_update",
                                        ),
                                        path(
                                            "delete/",
                                            MapUserLocationTypeDeleteView.as_view(),
                                            name="map_user_location_type_delete",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "external/",
                    include(
                        [
                            path(
                                "create/",
                                MapExternalLayerCreateView.as_view(),
                                name="map_external_layer_create",
                            ),
                            path(
                                "<uuid:external_layer_uuid>/",
                                include(
                                    [
                                        path(
                                            "delete/",
                                            MapExternalLayerDeleteView.as_view(),
                                            name="map_external_layer_delete",
                                        ),
                                        path(
                                            "update/",
                                            MapExternalLayerUpdateView.as_view(),
                                            name="map_external_layer_update",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "<slug:layer_slug>/",
                    include(
                        [
                            path(
                                "",
                                MapFeatureListView.as_view(),
                                name="map_features_list",
                            ),
                            path(
                                "create/",
                                MapFeatureCreateView.as_view(),
                                name="map_feature_create",
                            ),
                            path(
                                "import/",
                                MapLayerFeaturesImportView.as_view(),
                                name="map_layer_features_import",
                            ),
                            path(
                                "update/",
                                MapLayerUpdateView.as_view(),
                                name="map_layer_update",
                            ),
                            path(
                                "delete/",
                                MapLayerDeleteView.as_view(),
                                name="map_layer_delete",
                            ),
                            path(
                                "features/<uuid:feature_uuid>/",
                                include(
                                    [
                                        path(
                                            "update/",
                                            MapFeatureUpdateView.as_view(),
                                            name="map_feature_update",
                                        ),
                                        path(
                                            "delete/",
                                            MapFeatureDeleteView.as_view(),
                                            name="map_feature_delete",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "facilities/",
        include(
            [
                path("", FacilityListView.as_view(), name="facility_list"),
                path("create/", FacilityCreateView.as_view(), name="facility_create"),
                path(
                    "<uuid:facility_uuid>/",
                    include(
                        [
                            path(
                                "",
                                FacilityDetailView.as_view(),
                                name="facility_detail",
                            ),
                            path(
                                "update/",
                                FacilityUpdateView.as_view(),
                                name="facility_update",
                            ),
                            path(
                                "delete/",
                                FacilityDeleteView.as_view(),
                                name="facility_delete",
                            ),
                            path(
                                "opening_hours/",
                                include(
                                    [
                                        path(
                                            "create/",
                                            FacilityOpeningHoursCreateView.as_view(),
                                            name="facility_opening_hours_create",
                                        ),
                                        path(
                                            "<int:pk>/",
                                            include(
                                                [
                                                    path(
                                                        "update/",
                                                        FacilityOpeningHoursUpdateView.as_view(),
                                                        name="facility_opening_hours_update",
                                                    ),
                                                    path(
                                                        "delete/",
                                                        FacilityOpeningHoursDeleteView.as_view(),
                                                        name="facility_opening_hours_delete",
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    # feedback
    path("feedback_list/", EventFeedbackListView.as_view(), name="feedback_list"),
    path("feedback_detail/<uuid:pk>/", EventFeedbackDetailView.as_view(), name="feedback_detail"),
    path("feedback_process/<uuid:pk>/<str:state>", EventFeedbackProcessView.as_view(), name="feedback_process"),
    # infodesk
    path(
        "infodesk/",
        include(
            [
                path(
                    "scan_tickets/",
                    include(
                        [
                            path(
                                "",
                                ScanTicketsPosSelectView.as_view(),
                                name="scan_tickets_pos_select",
                            ),
                            path(
                                "<slug:pos_slug>/",
                                ScanTicketsView.as_view(),
                                name="scan_tickets",
                            ),
                        ],
                    ),
                ),
                path(
                    "scan_inventory/",
                    include(
                        [
                            path(
                                "",
                                ScanInventoryIndexView.as_view(),
                                name="scan_inventory_index",
                            ),
                            path(
                                "<slug:pos_slug>/",
                                ScanInventoryView.as_view(),
                                name="scan_inventory",
                            ),
                        ],
                    ),
                ),
                path(
                    "orders/",
                    include(
                        [
                            path("", OrderListView.as_view(), name="order_list"),
                            path(
                                "<int:order_id>/",
                                include(
                                    [
                                        path(
                                            "",
                                            OrderDetailView.as_view(),
                                            name="order_detail",
                                        ),
                                        path(
                                            "update/",
                                            OrderUpdateView.as_view(),
                                            name="order_update",
                                        ),
                                        path(
                                            "refund/",
                                            OrderRefundView.as_view(),
                                            name="order_refund",
                                        ),
                                        path(
                                            "download_proforma_invoice/",
                                            OrderDownloadProformaInvoiceView.as_view(),
                                            name="order_download_proforma_invoice",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "refunds/",
                    include(
                        [
                            path(
                                "",
                                RefundListView.as_view(),
                                name="refund_list",
                            ),
                            path(
                                "<int:refund_id>/",
                                include(
                                    [
                                        path(
                                            "",
                                            RefundDetailView.as_view(),
                                            name="refund_detail",
                                        ),
                                        path(
                                            "update/",
                                            RefundUpdateView.as_view(),
                                            name="refund_update",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "invoices/",
                    include(
                        [
                            path("", InvoiceListView.as_view(), name="invoice_list"),
                            path(
                                "csv/",
                                InvoiceListCSVView.as_view(),
                                name="invoice_list_csv",
                            ),
                            path(
                                "download/",
                                InvoiceDownloadMultipleView.as_view(),
                                name="invoice_download_multiple",
                            ),
                            path(
                                "<int:invoice_id>/",
                                include(
                                    [
                                        path(
                                            "download/",
                                            InvoiceDownloadView.as_view(),
                                            name="invoice_download",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "creditnotes/",
                    include(
                        [
                            path(
                                "",
                                CreditNoteListView.as_view(),
                                name="credit_note_list",
                            ),
                            path(
                                "<int:credit_note_id>/",
                                include(
                                    [
                                        path(
                                            "download",
                                            CreditNoteDownloadView.as_view(),
                                            name="credit_note_download",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path("shop_tickets/", ShopTicketOverview.as_view(), name="shop_ticket_overview"),
    # public names
    path(
        "public_credit_names/",
        ApproveNamesView.as_view(),
        name="public_credit_names",
    ),
    # merchandise orders
    path(
        "merchandise_orders/",
        MerchandiseOrdersView.as_view(),
        name="merchandise_orders",
    ),
    path(
        "merchandise_orders_labels/",
        MerchandiseOrdersLabelsView.as_view(),
        name="merchandise_orders_labels",
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
                    "pending/",
                    PendingProposalsView.as_view(),
                    name="pending_proposals",
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
                                    ],
                                ),
                            ),
                        ],
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
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
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
                                    ],
                                ),
                            ),
                        ],
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
                        ],
                    ),
                ),
            ],
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
                        ],
                    ),
                ),
            ],
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
                                "",
                                SpeakerDetailView.as_view(),
                                name="speaker_detail",
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
                        ],
                    ),
                ),
            ],
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
            ],
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
                        ],
                    ),
                ),
            ],
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
                            path(
                                "",
                                EventDetailView.as_view(),
                                name="event_detail",
                            ),
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
                        ],
                    ),
                ),
            ],
        ),
    ),
    # manage AutoScheduler
    path(
        "autoscheduler/",
        include(
            [
                path(
                    "",
                    AutoScheduleManageView.as_view(),
                    name="autoschedule_manage",
                ),
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
                    "diff/",
                    AutoScheduleDiffView.as_view(),
                    name="autoschedule_diff",
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
            ],
        ),
    ),
    # approve EventFeedback objects
    path(
        "approve_feedback",
        ApproveFeedbackView.as_view(),
        name="approve_event_feedback",
    ),
    # add recording url objects
    path(
        "add_recording",
        AddRecordingView.as_view(),
        name="add_eventrecording",
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
                                    ],
                                ),
                            ),
                        ],
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
                                include(
                                    [
                                        path("", ExpenseDetailView.as_view(), name="expense_detail"),
                                        path("update/", ExpenseUpdateView.as_view(), name="expense_update"),
                                    ],
                                ),
                            ),
                        ],
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
                                include(
                                    [
                                        path(
                                            "",
                                            RevenueDetailView.as_view(),
                                            name="revenue_detail",
                                        ),
                                        path(
                                            "update/",
                                            RevenueUpdateView.as_view(),
                                            name="revenue_update",
                                        ),
                                    ],
                                ),
                            ),
                        ],
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
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "banks/",
                    include(
                        [
                            path("", BankListView.as_view(), name="bank_list"),
                            path(
                                "<uuid:bank_uuid>/",
                                include(
                                    [
                                        path(
                                            "",
                                            BankDetailView.as_view(),
                                            name="bank_detail",
                                        ),
                                        path(
                                            "upload-csv/",
                                            BankCSVUploadView.as_view(),
                                            name="bank_csvupload",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "bankaccounts/",
                    include(
                        [
                            path(
                                "<uuid:bankaccount_uuid>/",
                                BankAccountDetailView.as_view(),
                                name="bankaccount_detail",
                            ),
                        ],
                    ),
                ),
                path(
                    "banktransactions/",
                    include(
                        [
                            path(
                                "<uuid:banktransaction_uuid>/",
                                BankTransactionDetailView.as_view(),
                                name="banktransaction_detail",
                            ),
                        ],
                    ),
                ),
                path(
                    "coinify/",
                    include(
                        [
                            path(
                                "",
                                CoinifyDashboardView.as_view(),
                                name="coinify_dashboard",
                            ),
                            path(
                                "payment_intents/",
                                CoinifyPaymentIntentListView.as_view(),
                                name="coinifypayment_intent_list",
                            ),
                            path(
                                "settlements/",
                                CoinifySettlementListView.as_view(),
                                name="coinifysettlement_list",
                            ),
                            path(
                                "invoices/",
                                CoinifyInvoiceListView.as_view(),
                                name="coinifyinvoice_list",
                            ),
                            path(
                                "payouts/",
                                CoinifyPayoutListView.as_view(),
                                name="coinifypayout_list",
                            ),
                            path(
                                "balances/",
                                CoinifyBalanceListView.as_view(),
                                name="coinifybalance_list",
                            ),
                            path(
                                "csv_import/",
                                CoinifyCSVImportView.as_view(),
                                name="coinify_csv_import",
                            ),
                        ],
                    ),
                ),
                path(
                    "epay/",
                    include(
                        [
                            path(
                                "",
                                EpayTransactionListView.as_view(),
                                name="epaytransaction_list",
                            ),
                            path(
                                "csv_import/",
                                EpayCSVImportView.as_view(),
                                name="epay_csv_import",
                            ),
                        ],
                    ),
                ),
                path(
                    "clearhaus/",
                    include(
                        [
                            path(
                                "",
                                ClearhausSettlementListView.as_view(),
                                name="clearhaussettlement_list",
                            ),
                            path(
                                "csv_import/",
                                ClearhausSettlementImportView.as_view(),
                                name="clearhaus_csv_import",
                            ),
                            path(
                                "<uuid:settlement_uuid>/",
                                ClearhausSettlementDetailView.as_view(),
                                name="clearhaussettlement_detail",
                            ),
                        ],
                    ),
                ),
                path(
                    "zettle/",
                    include(
                        [
                            path(
                                "",
                                ZettleDashboardView.as_view(),
                                name="zettle_dashboard",
                            ),
                            path(
                                "receipts/",
                                ZettleReceiptListView.as_view(),
                                name="zettlereceipt_list",
                            ),
                            path(
                                "balances/",
                                ZettleBalanceListView.as_view(),
                                name="zettlebalance_list",
                            ),
                            path(
                                "import/",
                                ZettleDataImportView.as_view(),
                                name="zettle_import",
                            ),
                        ],
                    ),
                ),
                path(
                    "mobilepay/",
                    include(
                        [
                            path(
                                "",
                                MobilePayTransactionListView.as_view(),
                                name="mobilepaytransaction_list",
                            ),
                            path(
                                "csv_import/",
                                MobilePayCSVImportView.as_view(),
                                name="mobilepay_csv_import",
                            ),
                        ],
                    ),
                ),
                path(
                    "accounting_export/",
                    include(
                        [
                            path(
                                "",
                                AccountingExportListView.as_view(),
                                name="accountingexport_list",
                            ),
                            path(
                                "create/",
                                AccountingExportCreateView.as_view(),
                                name="accountingexport_create",
                            ),
                            path(
                                "<uuid:accountingexport_uuid>/",
                                include(
                                    [
                                        path(
                                            "",
                                            AccountingExportDetailView.as_view(),
                                            name="accountingexport_detail",
                                        ),
                                        path(
                                            "download/",
                                            include(
                                                [
                                                    path(
                                                        "",
                                                        AccountingExportDownloadArchiveView.as_view(),
                                                        name="accountingexport_download_archive",
                                                    ),
                                                    path(
                                                        "<str:filename>",
                                                        AccountingExportDownloadFileView.as_view(),
                                                        name="accountingexport_download_file",
                                                    ),
                                                ],
                                            ),
                                        ),
                                        path(
                                            "update/",
                                            AccountingExportUpdateView.as_view(),
                                            name="accountingexport_update",
                                        ),
                                        path(
                                            "delete/",
                                            AccountingExportDeleteView.as_view(),
                                            name="accountingexport_delete",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    # release held emails
    path(
        "release_emails",
        OutgoingEmailMassUpdateView.as_view(),
        name="outgoing_email_release",
    ),
    # point-of-sale
    path(
        "pos/",
        include(
            [
                path(
                    "",
                    PosListView.as_view(),
                    name="pos_list",
                ),
                path(
                    "create/",
                    PosCreateView.as_view(),
                    name="pos_create",
                ),
                path(
                    "products/",
                    include(
                        [
                            path(
                                "",
                                PosProductListView.as_view(),
                                name="posproduct_list",
                            ),
                            path(
                                "<uuid:posproduct_uuid>/update/",
                                PosProductUpdateView.as_view(),
                                name="posproduct_update",
                            ),
                        ],
                    ),
                ),
                path(
                    "product_costs/",
                    include(
                        [
                            path(
                                "",
                                PosProductCostListView.as_view(),
                                name="posproductcost_list",
                            ),
                            path(
                                "<uuid:posproductcost_uuid>/update/",
                                PosProductCostUpdateView.as_view(),
                                name="posproductcost_update",
                            ),
                        ],
                    ),
                ),
                path(
                    "transactions/",
                    PosTransactionListView.as_view(),
                    name="postransaction_list",
                ),
                path(
                    "sales/",
                    PosSaleListView.as_view(),
                    name="possale_list",
                ),
                path(
                    "sales/import/",
                    PosSalesImportView.as_view(),
                    name="possale_import",
                ),
                path(
                    "<slug:pos_slug>/",
                    include(
                        [
                            path(
                                "",
                                PosDetailView.as_view(),
                                name="pos_detail",
                            ),
                            path(
                                "update/",
                                PosUpdateView.as_view(),
                                name="pos_update",
                            ),
                            path(
                                "delete/",
                                PosDeleteView.as_view(),
                                name="pos_delete",
                            ),
                            path(
                                "reports/",
                                include(
                                    [
                                        path(
                                            "",
                                            PosReportListView.as_view(),
                                            name="posreport_list",
                                        ),
                                        path(
                                            "create/",
                                            PosReportCreateView.as_view(),
                                            name="posreport_create",
                                        ),
                                        path(
                                            "<uuid:posreport_uuid>/",
                                            include(
                                                [
                                                    path(
                                                        "",
                                                        PosReportDetailView.as_view(),
                                                        name="posreport_detail",
                                                    ),
                                                    path(
                                                        "update/",
                                                        PosReportUpdateView.as_view(),
                                                        name="posreport_update",
                                                    ),
                                                    path(
                                                        "bankcount/start/",
                                                        PosReportBankCountStartView.as_view(),
                                                        name="posreport_bank_count_start",
                                                    ),
                                                    path(
                                                        "bankcount/end/",
                                                        PosReportBankCountEndView.as_view(),
                                                        name="posreport_bank_count_end",
                                                    ),
                                                    path(
                                                        "poscount/start/",
                                                        PosReportPosCountStartView.as_view(),
                                                        name="posreport_pos_count_start",
                                                    ),
                                                    path(
                                                        "poscount/end/",
                                                        PosReportPosCountEndView.as_view(),
                                                        name="posreport_pos_count_end",
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    # tokens
    path(
        "tokens/",
        include(
            [
                path(
                    "",
                    TokenListView.as_view(),
                    name="token_list",
                ),
                path(
                    "create/",
                    TokenCreateView.as_view(),
                    name="token_create",
                ),
                path(
                    "stats/",
                    TokenStatsView.as_view(),
                    name="token_stats",
                ),
                path(
                    "<int:pk>/",
                    include(
                        [
                            path(
                                "",
                                TokenDetailView.as_view(),
                                name="token_detail",
                            ),
                            path(
                                "update/",
                                TokenUpdateView.as_view(),
                                name="token_update",
                            ),
                            path(
                                "delete/",
                                TokenDeleteView.as_view(),
                                name="token_delete",
                            ),
                        ],
                    ),
                ),
                path(
                    "categories/",
                    include(
                        [
                            path(
                                "",
                                TokenCategoryListView.as_view(),
                                name="token_category_list",
                            ),
                            path(
                                "create/",
                                TokenCategoryCreateView.as_view(),
                                name="token_category_create",
                            ),
                            path(
                                "<int:pk>/",
                                include(
                                    [
                                        path(
                                            "",
                                            TokenCategoryDetailView.as_view(),
                                            name="token_category_detail",
                                        ),
                                        path(
                                            "update/",
                                            TokenCategoryUpdateView.as_view(),
                                            name="token_category_update",
                                        ),
                                        path(
                                            "delete/",
                                            TokenCategoryDeleteView.as_view(),
                                            name="token_category_delete",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path(
        "irc/",
        include([path("overview/", IrcOverView.as_view(), name="irc_overview")]),
    ),
    path(
        "shop_ticket_stats/",
        include(
            [
                path("", ShopTicketStatsView.as_view(), name="shop_ticket_stats"),
                path(
                    "<uuid:pk>/",
                    ShopTicketStatsDetailView.as_view(),
                    name="shop_ticket_stats_detail",
                ),
            ],
        ),
    ),
    # team permissions
    path(
        "team_permissions/",
        include(
            [
                path(
                    "",
                    TeamPermissionIndexView.as_view(),
                    name="team_permission_index",
                ),
                path(
                    "<slug:team_slug>/",
                    TeamPermissionManageView.as_view(),
                    name="team_permission_manage",
                ),
            ],
        ),
    ),
    path(
        "permissions/",
        include(
            [
                path(
                    "by_group/",
                    PermissionByGroupView.as_view(),
                    name="permission_list_by_group",
                ),
                path(
                    "by_user/",
                    PermissionByUserView.as_view(),
                    name="permission_list_by_user",
                ),
                path(
                    "by_permission/",
                    PermissionByPermissionView.as_view(),
                    name="permission_list_by_permission",
                ),
            ],
        ),
    ),
]
