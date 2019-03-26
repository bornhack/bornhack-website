from django.urls import path

from .views import ProfileDetail, ProfileUpdate, ProfileTokenFindsView

app_name = 'profiles'
urlpatterns = [
    path('', ProfileDetail.as_view(), name='detail'),
    path('edit', ProfileUpdate.as_view(), name='update'),
    path(
        'tokens',
        ProfileTokenFindsView.as_view(),
        name='tokenfind_list'
    ),
]
