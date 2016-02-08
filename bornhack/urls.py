# from allauth.account.views import (
#     SignupView,
#     LoginView,
#     LogoutView,
#     ConfirmEmailView,
#     EmailVerificationSentView,
#     PasswordResetView
# )
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    url(
        r'$^',
        TemplateView.as_view(template_name='frontpage.html'),
        name='frontpage'
    ),
    # url(
    #     r'^login/$',
    #     LoginView.as_view(),
    #     name='account_login',
    # ),
    # url(
    #     r'^logout/$',
    #     LogoutView.as_view(),
    #     name='account_logout',
    # ),
    # url(
    #     r'^confirm/(?P<key>\S+)$',
    #     ConfirmEmailView.as_view(),
    #     name='account_confirm_email',
    # ),
    # url(
    #     r'^signup/done/$',
    #     EmailVerificationSentView.as_view(),
    #     name='account_email_verification_sent',
    # ),
    # url(
    #     r'^signup/$',
    #     SignupView.as_view(),
    #     name='account_signup',
    # ),
    # url(
    #     r'^reset-password/$',
    #     PasswordResetView.as_view(),
    #     name='account_reset_password',
    # ),
    # url(
    #     r'^profile/',
    #     include('profiles.urls', namespace='profiles')
    # ),

    url(r'^admin/', include(admin.site.urls)),
]
