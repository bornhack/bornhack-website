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
from django.views.generic import TemplateView

urlpatterns = [
    url(
        r'^$',
        TemplateView.as_view(template_name='frontpage.html'),
        name='frontpage'
    ),
    url(
        r'good-to-know/',
        TemplateView.as_view(template_name='good_to_know.html'),
        name='good-to-know'
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
        r'^profile/',
        include('profiles.urls', namespace='profiles')
    ),
    url(
        r'^shop/',
        include('shop.urls', namespace='shop')
    ),
    url(r'^accounts/', include('allauth.urls')),

    url(r'^admin/', include(admin.site.urls)),
]
