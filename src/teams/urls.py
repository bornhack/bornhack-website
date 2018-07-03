from django.urls import path, include

from teams.views.base import (
    TeamListView,
    TeamMemberRemoveView,
    TeamMemberApproveView,
    TeamDetailView,
    TeamJoinView,
    TeamLeaveView,
    TeamManageView,
    FixIrcAclView,
)
from teams.views.info import InfoItemUpdateView, InfoItemCreateView, InfoItemDeleteView

from teams.views.tasks import (
    TaskCreateView,
    TaskDetailView,
    TaskUpdateView,
)

from teams.views.shifts import (
    ShiftListView,
    ShiftCreateView,
    ShiftUpdateView,
)

app_name = 'teams'

urlpatterns = [
    path(
        '',
        TeamListView.as_view(),
        name='list'
    ),
    path(
        'members/', include([
            path(
                '<int:pk>/remove/',
                TeamMemberRemoveView.as_view(),
                name='teammember_remove',
            ),
            path(
                '<int:pk>/approve/',
                TeamMemberApproveView.as_view(),
                name='teammember_approve',
            ),
        ]),
    ),
    path(
        '<slug:team_slug>/', include([
            path(
                '',
                TeamDetailView.as_view(),
                name='detail'
            ),
            path(
                'join/',
                TeamJoinView.as_view(),
                name='join'
            ),
            path(
                'leave/',
                TeamLeaveView.as_view(),
                name='leave'
            ),
            path(
                'manage/',
                TeamManageView.as_view(),
                name='manage'
            ),
            path(
                'fix_irc_acl/',
                FixIrcAclView.as_view(),
                name='fix_irc_acl',
            ),
            path(
                'tasks/', include([
                    path(
                        'create/',
                        TaskCreateView.as_view(),
                        name='task_create',
                    ),
                    path(
                        '<slug:slug>/', include([
                            path(
                                '',
                                TaskDetailView.as_view(),
                                name='task_detail',
                            ),
                            path(
                                'update/',
                                TaskUpdateView.as_view(),
                                name='task_update',
                            ),
                        ]),
                    ),

                ]),
            ),
            path(
                'info/<slug:category_anchor>/', include([
                    path(
                        'create/',
                        InfoItemCreateView.as_view(),
                        name='info_item_create',
                    ),
                    path(
                        '<slug:item_anchor>/', include([
                            path(
                                'update/',
                                InfoItemUpdateView.as_view(),
                                name='info_item_update',
                            ),
                            path(
                                'delete/',
                                InfoItemDeleteView.as_view(),
                                name='info_item_delete',
                            ),
                        ]),
                    ),
                ])
            ),
            path('shifts/', include([
                path(
                    '',
                    ShiftListView.as_view(),
                    name="shift_list"
                ),
                path(
                    'create/',
                    ShiftCreateView.as_view(),
                    name="shift_create"
                ),
                path(
                    '<int:pk>/',
                    ShiftUpdateView.as_view(),
                    name="shift_update"
                )
            ]))
        ]),
    ),
]

