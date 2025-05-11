from django.urls import path

from .views import ProfileApiView
from .views import ProfileDetail
from .views import ProfileOIDCView
from .views import ProfilePermissionList
from .views import ProfileSessionThemeSwitchView
from .views import ProfileUpdate

app_name = "profiles"
urlpatterns = [
    path("", ProfileDetail.as_view(), name="detail"),
    path("theme/", ProfileSessionThemeSwitchView.as_view(), name="theme"),
    path("edit/", ProfileUpdate.as_view(), name="update"),
    path("api/", ProfileApiView.as_view(), name="api"),
    path("permissions/", ProfilePermissionList.as_view(), name="permissions_list"),
    path("oidc/", ProfileOIDCView.as_view(), name="oidc"),
]
