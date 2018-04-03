from django.conf.urls import url
from .views import *


app_name = 'backoffice'

urlpatterns = [
    url(r'^$', BackofficeIndexView.as_view(), name='index'),
    url(r'product_handout/$', ProductHandoutView.as_view(), name='product_handout'),
    url(r'badge_handout/$', BadgeHandoutView.as_view(), name='badge_handout'),
    url(r'ticket_checkin/$', TicketCheckinView.as_view(), name='ticket_checkin'),
]

