from django.urls import include, path

from .views import (
    FacilityDetailView,
    FacilityFeedbackView,
    FacilityListView,
    FacilityTypeListView,
)

app_name = "facilities"
urlpatterns = [
    path("", FacilityTypeListView.as_view(), name="facility_type_list"),
    path(
        "<slug:facility_type_slug>/",
        include(
            [
                path("", FacilityListView.as_view(), name="facility_list"),
                path(
                    "<uuid:facility_uuid>/",
                    include(
                        [
                            path(
                                "", FacilityDetailView.as_view(), name="facility_detail"
                            ),
                            path(
                                "feedback/",
                                FacilityFeedbackView.as_view(),
                                name="facility_feedback",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
