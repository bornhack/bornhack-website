from django.urls import re_path
from .views import TokenDetailView

app_name = 'tokens'

urlpatterns = [
    re_path(
        '(?P<token>[0-9a-zA-Z\.@]+)/$',
        TokenDetailView.as_view(),
        name='details'
    ),
]

