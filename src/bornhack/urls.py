from django.conf.urls.static import static
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
                        r'^ics/', ICSView.as_view(), name="ics_view"
                    ),
                    url(
                        r'^proposals/', include([
                            url(
                                r'^$',
                                ProposalListView.as_view(),
                                name='proposal_list',
                            ),
                            url(
                                r'^speakers/', include([
                                   url(
                                        r'^create/$',
                                        SpeakerProposalCreateView.as_view(),
                                        name='speakerproposal_create'
                                    ),
                                    url(
                                        r'^(?P<pk>[a-f0-9-]+)/$',
                                        SpeakerProposalDetailView.as_view(),
                                        name='speakerproposal_detail'
                                    ),
                                    url(
                                        r'^(?P<pk>[a-f0-9-]+)/edit/$',
                                        SpeakerProposalUpdateView.as_view(),
                                        name='speakerproposal_update'
                                    ),
                                    url(
                                        r'^(?P<pk>[a-f0-9-]+)/submit/$',
                                        SpeakerProposalSubmitView.as_view(),
                                        name='speakerproposal_submit'
                                    ),
                                    url(
                                        r'^(?P<pk>[a-f0-9-]+)/pictures/(?P<picture>[-_\w+]+)/$',
                                        SpeakerProposalPictureView.as_view(),
                                        name='speakerproposal_picture',
                                    ),
                                ])
                            ),
                            url(
                                r'^events/', include([
                                    url(
                                        r'^create/$',
                                        EventProposalCreateView.as_view(),
                                        name='eventproposal_create'
                                    ),
                                    url(
                                        r'^(?P<pk>[a-f0-9-]+)/$',
                                        EventProposalDetailView.as_view(),
                                        name='eventproposal_detail'
                                    ),
                                    url(
                                        r'^(?P<pk>[a-f0-9-]+)/edit/$',
                                        EventProposalUpdateView.as_view(),
                                        name='eventproposal_update'
                                    ),
                                    url(
                                        r'^(?P<pk>[a-f0-9-]+)/submit/$',
                                        EventProposalSubmitView.as_view(),
                                        name='eventproposal_submit'
                                    ),
                                ])
                            ),
                        ])
                    ),
                    url(
                        r'^speakers/', include([
                            url(
                                r'^$',
                                SpeakerListView.as_view(),
                                name='speaker_index'
                            ),
                            url(
                                r'^(?P<slug>[-_\w+]+)/$',
                                SpeakerDetailView.as_view(),
                                name='speaker_detail'
                            ),
                            url(
                                r'^(?P<slug>[-_\w+]+)/pictures/(?P<picture>[-_\w+]+)/$',
                                SpeakerPictureView.as_view(),
                                name='speaker_picture',
                            ),
                        ]),
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
                        r'^calendar/',
                        ICSView.as_view(),
                        name='ics_calendar'
                    ),
                    # this has to be the last URL here
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

            url(
                r'^teams/', include([
                    url(
                        r'^$',
                        TeamListView.as_view(),
                        name='team_list'
                    ),
                    url(
                        r'^members/(?P<pk>[0-9]+)/remove/$',
                        TeamMemberRemoveView.as_view(),
                        name='teammember_remove',
                    ),
                    url(
                        r'^members/(?P<pk>[0-9]+)/approve/$',
                        TeamMemberApproveView.as_view(),
                        name='teammember_approve',
                    ),
                    url(
                        r'(?P<slug>[-_\w+]+)/join/$',
                        TeamJoinView.as_view(),
                        name='team_join'
                    ),
                    url(
                        r'(?P<slug>[-_\w+]+)/leave/$',
                        TeamLeaveView.as_view(),
                        name='team_leave'
                    ),
                    url(
                        r'(?P<slug>[-_\w+]+)/manage/$',
                        TeamManageView.as_view(),
                        name='team_manage'
                    ),
                    # this has to be the last url in the list
                    url(
                        r'(?P<slug>[-_\w+]+)/$',
                        TeamDetailView.as_view(),
                        name='team_detail'
                    ),
                ])
            ),
        ])
    )
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
