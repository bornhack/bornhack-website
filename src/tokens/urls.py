from django.urls import path, re_path

from .views import TokenFindListView, TokenFindView

app_name = "tokens"

urlpatterns = [
    path("", TokenFindListView.as_view(), name="tokenfind_list"),
    re_path(
        r"(?P<token>[0-9a-zA-Z\.@]{31,32})/$", TokenFindView.as_view(), name="details"
    ),
]
