from allauth.account.views import LoginView, LogoutView
from bar.views import MenuView
from camps.views import CampDetailView, CampListView, CampRedirectView
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from feedback.views import FeedbackCreate
from graphene_django.views import GraphQLView
from info.views import CampInfoView
from people.views import PeopleView
from sponsors.views import SponsorsView
from villages.views import (
    VillageCreateView,
    VillageDeleteView,
    VillageDetailView,
    VillageListView,
    VillageUpdateView,
)

# require 2fa token entry (if enabled on admin account) when logging into /admin by using allauth login form
admin.site.login = login_required(admin.site.login)

urlpatterns = [
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("profile/", include("allauth.urls")),
    path("profile/", include("allauth_2fa.urls")),
    path("profile/", include("profiles.urls", namespace="profiles")),
    path("tickets/", include("tickets.urls", namespace="tickets")),
    path("shop/", include("shop.urls", namespace="shop")),
    path("news/", include("news.urls", namespace="news")),
    path(
        "contact/", TemplateView.as_view(template_name="contact.html"), name="contact"
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
    # We don't need CSRF checks for the API
    path("api/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path("camps/", CampListView.as_view(), name="camp_list"),
    path("token/", include("tokens.urls", namespace="tokens")),
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
        CampRedirectView.as_view(),
        kwargs={"page": "sponsors"},
        name="sponsors_redirect",
    ),
    path(
        "villages/",
        CampRedirectView.as_view(),
        kwargs={"page": "village_list"},
        name="village_list_redirect",
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
                path("bar/menu/", MenuView.as_view(), name="menu"),
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
                        ]
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
            ]
        ),
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
