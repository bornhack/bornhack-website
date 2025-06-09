from __future__ import annotations

from django.urls import include
from django.urls import path

from .views import FacilityDetailView
from .views import FacilityFeedbackView
from .views import FacilityListGeoJSONView
from .views import FacilityListView
from .views import FacilityTypeListView

app_name = "facilities"
urlpatterns = [
    path("", FacilityTypeListView.as_view(), name="facility_type_list"),
    path(
        "<slug:facility_type_slug>/",
        include(
            [
                path("", FacilityListView.as_view(), name="facility_list"),
                path(
                    "geojson/",
                    FacilityListGeoJSONView.as_view(),
                    name="facility_list_geojson",
                ),
                path(
                    "<uuid:facility_uuid>/",
                    include(
                        [
                            path(
                                "",
                                FacilityDetailView.as_view(),
                                name="facility_detail",
                            ),
                            path(
                                "feedback/",
                                FacilityFeedbackView.as_view(),
                                name="facility_feedback",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
]
