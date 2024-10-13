from django.urls import path

from .views import ProfileApiView
from .views import ProfileDetail
from .views import ProfileUpdate
from .views import ProfilePermissionList
from .views import ProfileThemeSelectView

app_name = "profiles"
urlpatterns = [
    path("", ProfileDetail.as_view(), name="detail"),
    path("edit/", ProfileUpdate.as_view(), name="update"),
    path("api/", ProfileApiView.as_view(), name="api"),
    path("permissions/", ProfilePermissionList.as_view(), name="permissions_list"),
    path("set_theme/<str:theme>/", ProfileThemeSelectView.as_view(), name="set_theme"),
]
