from django.urls import path, include

from .views import (
    RideList,
    RideCreate,
    RideDetail,
    RideUpdate,
    RideDelete,
    RideContactConfirm,
)

app_name = 'rideshare'

urlpatterns = [
    path(
        '',
        RideList.as_view(),
        name='list'
    ),
    path(
        'create/',
        RideCreate.as_view(),
        name='create'
    ),
    path(
        '<uuid:pk>/', include([
            path(
                '',
                RideDetail.as_view(),
                name='detail'
            ),
            path(
                'update/',
                RideUpdate.as_view(),
                name='update'
            ),
            path(
                'delete/',
                RideDelete.as_view(),
                name='delete'
            ),
            path(
                'confirm/',
                RideContactConfirm.as_view(),
                name='contact-confirm'
            ),
        ])
    )
]
