from django.urls import include, path

from .views import RideCreate, RideDelete, RideDetail, RideList, RideUpdate

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
            ]
        ),
    ),
]
