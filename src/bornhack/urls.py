from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from allauth.account.views import (
    LoginView,
    LogoutView,
)
from graphene_django.views import GraphQLView

from camps.views import *
from feedback.views import FeedbackCreate
from info.views import *
from villages.views import *
from program.views import *
from sponsors.views import *
from people.views import *
from bar.views import MenuView

urlpatterns = [
    path(
        'profile/',
        include('profiles.urls', namespace='profiles')
    ),
    path(
        'tickets/',
        include('tickets.urls', namespace='tickets')
    ),
    path(
        'shop/',
        include('shop.urls', namespace='shop')
    ),
    path(
        'news/',
        include('news.urls', namespace='news')
    ),
    path(
        'contact/',
        TemplateView.as_view(template_name='contact.html'),
        name='contact'
    ),
    path(
        'conduct/',
        TemplateView.as_view(template_name='coc.html'),
        name='conduct'
    ),
    path(
        'login/',
        LoginView.as_view(),
        name='account_login',
    ),
    path(
        'logout/',
        LogoutView.as_view(),
        name='account_logout',
    ),
    path(
        'privacy-policy/',
        TemplateView.as_view(template_name='legal/privacy_policy.html'),
        name='privacy-policy'
    ),
    path(
        'general-terms-and-conditions/',
        TemplateView.as_view(template_name='legal/general_terms_and_conditions.html'),
        name='general-terms'
    ),
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),

    # We don't need CSRF checks for the API
    path('api/', csrf_exempt(GraphQLView.as_view(graphiql=True))),

    path(
        'camps/',
        CampListView.as_view(),
        name='camp_list'
    ),

    path(
        'token/',
        include('tokens.urls', namespace='tokens'),
    ),

    # camp redirect views here

    path(
        '',
        CampRedirectView.as_view(),
        kwargs={'page': 'camp_detail'},
        name='camp_detail_redirect',
    ),

    path(
        'program/',
        CampRedirectView.as_view(),
        kwargs={'page': 'schedule_index'},
        name='schedule_index_redirect',
    ),

    path(
        'info/',
        CampRedirectView.as_view(),
        kwargs={'page': 'info'},
        name='info_redirect',
    ),

    path(
        'sponsors/',
        CampRedirectView.as_view(),
        kwargs={'page': 'sponsors'},
        name='sponsors_redirect',
    ),

    path(
        'villages/',
        CampRedirectView.as_view(),
        kwargs={'page': 'village_list'},
        name='village_list_redirect',
    ),

    path(
        'people/',
        PeopleView.as_view(),
        name='people',
    ),

    # camp specific urls below here

    path(
        '<slug:camp_slug>/', include([
            path(
                '',
                CampDetailView.as_view(),
                name='camp_detail'
            ),

            path(
                'info/',
                CampInfoView.as_view(),
                name='info'
            ),

            path(
                'program/',
                include('program.urls', namespace='program'),
            ),

            path(
                'sponsors/',
                SponsorsView.as_view(),
                name='sponsors'
            ),

            path(
                'bar/menu/',
                MenuView.as_view(),
                name='menu'
            ),

            path(
                'villages/', include([
                    path(
                        '',
                        VillageListView.as_view(),
                        name='village_list'
                    ),
                    path(
                        'create/',
                        VillageCreateView.as_view(),
                        name='village_create'
                    ),
                    path(
                        '<slug:slug>/delete/',
                        VillageDeleteView.as_view(),
                        name='village_delete'
                    ),
                    path(
                        '<slug:slug>/edit/',
                        VillageUpdateView.as_view(),
                        name='village_update'
                    ),
                    # this has to be the last url in the list
                    path(
                        '<slug:slug>/',
                        VillageDetailView.as_view(),
                        name='village_detail'
                    ),
                ])
            ),

            path(
                'teams/',
                include('teams.urls', namespace='teams')
            ),

            path(
                'rideshare/',
                include('rideshare.urls', namespace='rideshare')
            ),

            path(
                'backoffice/',
                include('backoffice.urls', namespace='backoffice')
            ),

            path(
                'feedback/',
                FeedbackCreate.as_view(),
                name='feedback'
            ),

            path(
                'economy/',
                include('economy.urls', namespace='economy'),
            ),
        ])
    )
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

