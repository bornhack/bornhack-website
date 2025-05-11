from allauth.account.views import LoginView
from allauth.account.views import LogoutView
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include
from django.urls import path
from django.views.generic import TemplateView

from camps.views import CampDetailView
from camps.views import CampListView
from camps.views import CampRedirectView
from contact.views import ContactView
from feedback.views import FeedbackCreate
from info.views import CampInfoView
from maps.views import MapView
from maps.views import LayerUserLocationView
from maps.views import UserLocationListView
from maps.views import UserLocationUpdateView
from maps.views import UserLocationCreateView
from maps.views import UserLocationDeleteView
from maps.views import UserLocationApiView
from people.views import PeopleView
from sponsors.views import AllSponsorsView
from sponsors.views import SponsorsView
from utils.views import csrfview
from villages.views import VillageCreateView
from villages.views import VillageDeleteView
from villages.views import VillageDetailView
from villages.views import VillageListGeoJSONView
from villages.views import VillageListView
from villages.views import VillageMapView
from villages.views import VillageUpdateView

# require 2fa token entry (if enabled on admin account) when logging into /admin by using allauth login form
admin.site.login = login_required(admin.site.login)

urlpatterns = [
    path("api/csrf/", csrfview),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("profile/", include("allauth.urls")),
    path("profile/", include("profiles.urls", namespace="profiles")),
    path("tickets/", include("tickets.urls", namespace="tickets")),
    path("shop/", include("shop.urls", namespace="shop")),
    path("news/", include("news.urls", namespace="news")),
    path(
        "contact/",
        ContactView.as_view(),
        name="contact",
    ),
    path("conduct/", TemplateView.as_view(template_name="coc.html"), name="conduct"),
    path("login/", LoginView.as_view(), name="account_login"),
    path("logout/", LogoutView.as_view(), name="account_logout"),
    path(
        "privacy-policy/",
        TemplateView.as_view(template_name="legal/privacy_policy.html"),
        name="privacy-policy",
    ),
    path(
        "general-terms-and-conditions/",
        TemplateView.as_view(template_name="legal/general_terms_and_conditions.html"),
        name="general-terms",
    ),
    path("admin/", admin.site.urls),
    path("camps/", CampListView.as_view(), name="camp_list"),
    path("token/", include("tokens.urls", namespace="tokens")),
    path("maps/", include("maps.urls", namespace="maps")),
    path("", include("django_prometheus.urls")),
    # camp redirect views here
    path(
        "",
        CampRedirectView.as_view(),
        kwargs={"page": "camp_detail"},
        name="camp_detail_redirect",
    ),
    path(
        "program/",
        CampRedirectView.as_view(),
        kwargs={"page": "program:schedule_index"},
        name="schedule_index_redirect",
    ),
    path(
        "info/",
        CampRedirectView.as_view(),
        kwargs={"page": "info"},
        name="info_redirect",
    ),
    path(
        "sponsors/",
        AllSponsorsView.as_view(),
        name="allsponsors",
    ),
    path(
        "villages/",
        CampRedirectView.as_view(),
        kwargs={"page": "village_list"},
        name="village_list_redirect",
    ),
    path(
        "teams/",
        CampRedirectView.as_view(),
        kwargs={"page": "teams:list"},
        name="teams_list_redirect",
    ),
    path(
        "rideshare/",
        CampRedirectView.as_view(),
        kwargs={"page": "rideshare:list"},
        name="rideshare_list_redirect",
    ),
    path(
        "feedback/",
        CampRedirectView.as_view(),
        kwargs={"page": "feedback"},
        name="feedback_redirect",
    ),
    path(
        "facilities/",
        CampRedirectView.as_view(),
        kwargs={"page": "facilities:facility_type_list"},
        name="facilities_list_redirect",
    ),
    path(
        "wishlist/",
        CampRedirectView.as_view(),
        kwargs={"page": "wishlist:list"},
        name="wish_list_redirect",
    ),
    path(
        "backoffice/",
        CampRedirectView.as_view(),
        kwargs={"page": "backoffice:index"},
        name="backoffice_redirect",
    ),
    path(
        "economy/",
        CampRedirectView.as_view(),
        kwargs={"page": "economy:dashboard"},
        name="economy_dashboard_redirect",
    ),
    path(
        "phonebook/",
        CampRedirectView.as_view(),
        kwargs={"page": "phonebook:list"},
        name="phone_book_redirect",
    ),
    path("people/", PeopleView.as_view(), name="people"),
    # camp specific urls below here
    path(
        "<slug:camp_slug>/",
        include(
            [
                path("", CampDetailView.as_view(), name="camp_detail"),
                path("info/", CampInfoView.as_view(), name="info"),
                path("program/", include("program.urls", namespace="program")),
                path("sponsors/", SponsorsView.as_view(), name="sponsors"),
                path(
                    "map/",
                    include(
                        [
                            path("", MapView.as_view(), name="maps_map"),
                            path(
                                "userlocation_geojson/<slug:user_location_type_slug>/",
                                LayerUserLocationView.as_view(),
                                name="maps_user_location_layer",
                            ),
                            path(
                                "userlocation/",
                                include(
                                    [
                                        path(
                                            "",
                                            UserLocationListView.as_view(),
                                            name="maps_user_location_list",
                                        ),
                                        path(
                                            "create/",
                                            UserLocationCreateView.as_view(),
                                            name="maps_user_location_create",
                                        ),
                                        path(
                                            "create/api/",
                                            UserLocationApiView.as_view(),
                                            name="maps_user_location_create_api",
                                        ),
                                        path(
                                            "<uuid:user_location>/",
                                            include(
                                                [
                                                    path(
                                                        "update/",
                                                        UserLocationUpdateView.as_view(),
                                                        name="maps_user_location_update",
                                                    ),
                                                    path(
                                                        "delete/",
                                                        UserLocationDeleteView.as_view(),
                                                        name="maps_user_location_delete",
                                                    ),
                                                    path(
                                                        "api/",
                                                        UserLocationApiView.as_view(),
                                                        name="maps_user_location_api",
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                path(
                    "villages/",
                    include(
                        [
                            path("", VillageListView.as_view(), name="village_list"),
                            path(
                                "create/",
                                VillageCreateView.as_view(),
                                name="village_create",
                            ),
                            path(
                                "geojson/",
                                VillageListGeoJSONView.as_view(),
                                name="villages_geojson",
                            ),
                            path(
                                "map/",
                                VillageMapView.as_view(),
                                name="villages_map",
                            ),
                            path(
                                "<slug:slug>/delete/",
                                VillageDeleteView.as_view(),
                                name="village_delete",
                            ),
                            path(
                                "<slug:slug>/edit/",
                                VillageUpdateView.as_view(),
                                name="village_update",
                            ),
                            # this has to be the last url in the list
                            path(
                                "<slug:slug>/",
                                VillageDetailView.as_view(),
                                name="village_detail",
                            ),
                        ],
                    ),
                ),
                path("teams/", include("teams.urls", namespace="teams")),
                path("rideshare/", include("rideshare.urls", namespace="rideshare")),
                path("backoffice/", include("backoffice.urls", namespace="backoffice")),
                path("feedback/", FeedbackCreate.as_view(), name="feedback"),
                path("economy/", include("economy.urls", namespace="economy")),
                path("wishlist/", include("wishlist.urls", namespace="wishlist")),
                path("facilities/", include("facilities.urls", namespace="facilities")),
                path("phonebook/", include("phonebook.urls", namespace="phonebook")),
            ],
        ),
    ),
]

if settings.DEBUG_TOOLBAR_ENABLED:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
