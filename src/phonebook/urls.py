from django.urls import include, path, re_path

from .views import (
    DectExportView,
    DectRegistrationCreateView,
    DectRegistrationDeleteView,
    DectRegistrationListView,
    DectRegistrationUpdateView,
    PhonebookListView,
)

app_name = "phonebook"
urlpatterns = [
    path("", PhonebookListView.as_view(), name="list"),
    path("csv/", DectExportView.as_view(), name="csv"),
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
                re_path(
                    r"^(?P<dect_number>\d{4,9})/",
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
