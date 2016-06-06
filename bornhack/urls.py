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

urlpatterns = [
    url(
        r'^$',
        TemplateView.as_view(template_name='frontpage.html'),
        name='frontpage'
    ),
    url(
        r'info/',
        TemplateView.as_view(template_name='info.html'),
        name='info'
    ),
    url(
        r'contact/',
        TemplateView.as_view(template_name='contact.html'),
        name='contact'
    ),
    url(
        r'conduct/',
        TemplateView.as_view(template_name='coc.html'),
        name='conduct'
    ),
    url(
        r'call-for-sponsors/',
        TemplateView.as_view(template_name='sponsors.html'),
        name='call-for-sponsors'
    ),
    url(r'^sponsors/$', RedirectView.as_view(url=reverse_lazy('call-for-sponsors'), permanent=True)),
    url(
        r'call-for-speakers/',
        TemplateView.as_view(template_name='speakers.html'),
        name='call-for-speakers'
    ),
    url(r'^speakers/$', RedirectView.as_view(url=reverse_lazy('call-for-speakers'), permanent=True)),
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
        r'privacy-policy/$',
        TemplateView.as_view(template_name='legal/privacy_policy.html'),
        name='privacy-policy'
    ),
    url(
        r'general-terms-and-conditions/$',
        TemplateView.as_view(template_name='legal/general_terms_and_conditions.html'),
        name='general-terms'
    ),
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
    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/', include(admin.site.urls)),

]
