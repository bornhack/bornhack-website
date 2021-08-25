from django.urls import path

from .views import (
    VillageDeleteView,
    VillageDetailView,
    VillageListView,
    VillageUpdateView,
)

app_name = "villages"

urlpatterns = [
    path("", VillageListView.as_view(), name="list"),
    # path("create/", VillageCreateView.as_view(), name="create"),
    path("<slug:slug>/delete/", VillageDeleteView.as_view(), name="delete"),
    path("<slug:slug>/edit/", VillageUpdateView.as_view(), name="update"),
    path("<slug:slug>/", VillageDetailView.as_view(), name="detail"),
]
