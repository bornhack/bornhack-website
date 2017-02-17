from allauth.account.views import (
    SignupView,
    LoginView,
    LogoutView,
    ConfirmEmailView,
    EmailVerificationSentView,
    PasswordResetView
)
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView, RedirectView
from django.core.urlresolvers import reverse_lazy
from camps.views import *
from info.views import *
from villages.views import *
from program.views import *
from sponsors.views import *

urlpatterns = [
    url(
        r'^profile/',
        include('profiles.urls', namespace='profiles')
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
        r'^$',
        TemplateView.as_view(template_name='frontpage.html'),
        name='frontpage'
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
                r'^program/', include([
                    url(
                        r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})/$',
                        ScheduleView.as_view(),
                        name='schedule_day'
                    ),
                    url(
                        r'^$',
                        ScheduleView.as_view(),
                        name='schedule_index'
                    ),
                    url(
                        r'^speakers/$',
                        SpeakerListView.as_view(),
                        name='speaker_index'
                    ),
                    url(
                        r'^speakers/(?P<slug>[-_\w+]+)/$',
                        SpeakerDetailView.as_view(),
                        name='speaker_detail'
                    ),
                    url(
                        r'^events/$',
                        EventListView.as_view(),
                        name='event_index'
                    ),
                    url(
                        r'^call-for-speakers/$',
                        CallForSpeakersView.as_view(),
                        name='call_for_speakers'
                    ),
                    url(
                        r'^(?P<slug>[-_\w+]+)/$',
                        EventDetailView.as_view(),
                        name='event_detail'
                    ),
               ])
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
                    url(
                        r'(?P<slug>[-_\w+]+)/$',
                        VillageDetailView.as_view(),
                        name='village_detail'
                    ),
                ])
            ),
        ])
    )
]

