from django.urls import include
from django.urls import path
from django.urls import re_path

from .views import DectExportView
from .views import DectRegistrationCreateView
from .views import DectRegistrationDeleteView
from .views import DectRegistrationListView
from .views import DectRegistrationUpdateView
from .views import PhonebookListView

app_name = "phonebook"
urlpatterns = [
    path("", PhonebookListView.as_view(), name="list"),
    path("csv/", DectExportView.as_view(), name="csv"),
    path(
        "dectregistrations/",
        include(
            [
                path(
                    "",
                    DectRegistrationListView.as_view(),
                    name="dectregistration_list",
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
                        ],
                    ),
                ),
            ],
        ),
    ),
]
