from __future__ import annotations

from django.urls import include
from django.urls import path

from .views import RideCreate
from .views import RideDelete
from .views import RideDetail
from .views import RideList
from .views import RideUpdate

app_name = "rideshare"

urlpatterns = [
    path("", RideList.as_view(), name="list"),
    path("create/", RideCreate.as_view(), name="create"),
    path(
        "<uuid:pk>/",
        include(
            [
                path("", RideDetail.as_view(), name="detail"),
                path("update/", RideUpdate.as_view(), name="update"),
                path("delete/", RideDelete.as_view(), name="delete"),
            ],
        ),
    ),
]
