from django.urls import path

from .views import ProfileApiView
from .views import ProfileDetail
from .views import ProfileUpdate
from .views import ProfilePermissionList
from .views import ProfileSessionThemeSwitchView

app_name = "profiles"
urlpatterns = [
    path("", ProfileDetail.as_view(), name="detail"),
    path("theme/", ProfileSessionThemeSwitchView.as_view(), name="theme"),
    path("edit/", ProfileUpdate.as_view(), name="update"),
    path("api/", ProfileApiView.as_view(), name="api"),
    path("permissions/", ProfilePermissionList.as_view(), name="permissions_list"),
]
