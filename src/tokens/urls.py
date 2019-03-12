from django.urls import path, re_path, include
from .views import TokenDetailView, TokenFindListView

app_name = 'tokens'

urlpatterns = [
    path(
        '',
        TokenFindListView.as_view(),
        name='tokenfind_list'
    ),
    re_path(
        '(?P<token>[0-9a-zA-Z\.@]+)/$',
        TokenDetailView.as_view(),
        name='details'
    ),
]

