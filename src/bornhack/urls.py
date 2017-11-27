from allauth.account.views import (
    LoginView,
    LogoutView,
)
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from camps.views import *
from info.views import *
from villages.views import *
from program.views import *
from sponsors.views import *
from teams.views import *
from people.views import *
from tickets.views import ShopTicketListView
from bar.views import MenuView

urlpatterns = [
    url(
        r'^profile/',
        include('profiles.urls', namespace='profiles')
    ),
    url(
        r'^tickets/',
        include('tickets.urls', namespace='tickets')
    ),
    url(
        r'^shop/',
        include('shop.urls', namespace='shop')
    ),
    url(
        r'^news/',
        include('news.urls', namespace='news')
    ),
    url(
        r'^contact/',
        TemplateView.as_view(template_name='contact.html'),
        name='contact'
    ),
    url(
        r'^conduct/',
        TemplateView.as_view(template_name='coc.html'),
        name='conduct'
    ),
    url(
        r'^login/$',
        LoginView.as_view(),
        name='account_login',
    ),
    url(
        r'^logout/$',
        LogoutView.as_view(),
        name='account_logout',
    ),
    url(
        r'^privacy-policy/$',
        TemplateView.as_view(template_name='legal/privacy_policy.html'),
        name='privacy-policy'
    ),
    url(
        r'^general-terms-and-conditions/$',
        TemplateView.as_view(template_name='legal/general_terms_and_conditions.html'),
        name='general-terms'
    ),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(
        r'^camps/$',
        CampListView.as_view(),
        name='camp_list'
    ),

    # camp redirect views here

    url(
        r'^$',
        CampRedirectView.as_view(),
        kwargs={'page': 'camp_detail'},
        name='camp_detail_redirect',
    ),

    url(
        r'^program/$',
        CampRedirectView.as_view(),
        kwargs={'page': 'schedule_index'},
        name='schedule_index_redirect',
    ),

    url(
        r'^info/$',
        CampRedirectView.as_view(),
        kwargs={'page': 'info'},
        name='info_redirect',
    ),

    url(
        r'^sponsors/$',
        CampRedirectView.as_view(),
        kwargs={'page': 'sponsors'},
        name='sponsors_redirect',
    ),

    url(
        r'^villages/$',
        CampRedirectView.as_view(),
        kwargs={'page': 'village_list'},
        name='village_list_redirect',
    ),

    url(
        r'^people/$',
        PeopleView.as_view(),
        name='people',
    ),

    url(
        r'^backoffice/',
        include('backoffice.urls', namespace='backoffice')
    ),

    # camp specific urls below here

    url(
        r'(?P<camp_slug>[-_\w+]+)/', include([
            url(
                r'^$',
                CampDetailView.as_view(),
                name='camp_detail'
            ),

            url(
                r'^info/$',
                CampInfoView.as_view(),
                name='info'
            ),

            url(
                r'^program/', include('program.urls')
            ),

            url(
                r'^sponsors/call/$',
                CallForSponsorsView.as_view(),
                name='call-for-sponsors'
            ),
            url(
                r'^sponsors/$',
                SponsorsView.as_view(),
                name='sponsors'
            ),

            url(
                r'^bar/menu$',
                MenuView.as_view(),
                name='menu'
            ),

            url(
                r'^villages/', include([
                    url(
                        r'^$',
                        VillageListView.as_view(),
                        name='village_list'
                    ),
                    url(
                        r'create/$',
                        VillageCreateView.as_view(),
                        name='village_create'
                    ),
                    url(
                        r'(?P<slug>[-_\w+]+)/delete/$',
                        VillageDeleteView.as_view(),
                        name='village_delete'
                    ),
                    url(
                        r'(?P<slug>[-_\w+]+)/edit/$',
                        VillageUpdateView.as_view(),
                        name='village_update'
                    ),
                    # this has to be the last url in the list
                    url(
                        r'(?P<slug>[-_\w+]+)/$',
                        VillageDetailView.as_view(),
                        name='village_detail'
                    ),
                ])
            ),

            url(
                r'^teams/',
                include('teams.urls', namespace='teams')
            ),


        ])
    )
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
