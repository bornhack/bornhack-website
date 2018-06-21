from django.urls import path, include
from .views import *


app_name = 'backoffice'

urlpatterns = [
    path('', BackofficeIndexView.as_view(), name='index'),
    path('product_handout/', ProductHandoutView.as_view(), name='product_handout'),
    path('badge_handout/', BadgeHandoutView.as_view(), name='badge_handout'),
    path('ticket_checkin/', TicketCheckinView.as_view(), name='ticket_checkin'),
    path('public_credit_names/', ApproveNamesView.as_view(), name='public_credit_names'),
    path('manage_proposals/', include([
        path('', ManageProposalsView.as_view(), name='manage_proposals'),
        path('speakers/<uuid:pk>/', SpeakerProposalManageView.as_view(), name='speakerproposal_manage'),
        path('events/<uuid:pk>/', EventProposalManageView.as_view(), name='eventproposal_manage'),
    ])),
]

