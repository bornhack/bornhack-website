from django.urls import include, path

from .views import (
    DectRegistrationCreateView,
    DectRegistrationDeleteView,
    DectRegistrationListView,
    DectRegistrationUpdateView,
    PhonebookListView,
)

app_name = "phonebook"
urlpatterns = [
    path("", PhonebookListView.as_view(), name="list"),
    path(
        "dectregistrations/",
        include(
            [
                path(
                    "", DectRegistrationListView.as_view(), name="dectregistration_list"
                ),
                path(
                    "create/",
                    DectRegistrationCreateView.as_view(),
                    name="dectregistration_create",
                ),
                path(
                    "<int:dect_number>/",
                    include(
                        [
                            path(
                                "update/",
                                DectRegistrationUpdateView.as_view(),
                                name="dectregistration_update",
                            ),
                            path(
                                "delete/",
                                DectRegistrationDeleteView.as_view(),
                                name="dectregistration_delete",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
