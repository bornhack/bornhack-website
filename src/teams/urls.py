from django.urls import path, include

from teams.views.base import (
    TeamListView,
    TeamGeneralView,
    TeamManageView,
    FixIrcAclView,
)

from teams.views.members import (
    TeamMembersView,
    TeamMemberRemoveView,
    TeamMemberApproveView,
    TeamJoinView,
    TeamLeaveView,
)

from teams.views.info import (
    InfoCategoriesListView,
    InfoItemUpdateView,
    InfoItemCreateView,
    InfoItemDeleteView,
)

from teams.views.tasks import (
    TeamTasksView,
    TaskCreateView,
    TaskDetailView,
    TaskUpdateView,
)

from teams.views.shifts import (
    ShiftListView,
    ShiftCreateView,
    ShiftCreateMultipleView,
    ShiftUpdateView,
    ShiftDeleteView,
    MemberTakesShift,
    MemberDropsShift,
    UserShifts,
)

from teams.views.guide import (
    TeamGuideView,
    TeamGuidePrintView
)

app_name = 'teams'

urlpatterns = [
    path(
        '',
        TeamListView.as_view(),
        name='list'
    ),
    path(
        'shifts',
        UserShifts.as_view(),
        name='user_shifts'
    ),
    path(
        '<slug:team_slug>/', include([
            path(
                '',
                TeamGeneralView.as_view(),
                name='general'
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
                'guide/',
                TeamGuideView.as_view(),
                name='guide'
            ),
            path(
                'guide/print/',
                TeamGuidePrintView.as_view(),
                name='guide_print'
            ),
            path(
                'fix_irc_acl/',
                FixIrcAclView.as_view(),
                name='fix_irc_acl',
            ),
            path(
                'members/', include([
                    path(
                        '',
                        TeamMembersView.as_view(),
                        name='members'
                    ),
                    path(
                        '<int:pk>/remove/',
                        TeamMemberRemoveView.as_view(),
                        name='member_remove',
                    ),
                    path(
                        '<int:pk>/approve/',
                        TeamMemberApproveView.as_view(),
                        name='member_approve',
                    ),
                ]),
            ),
            path(
                'tasks/', include([
                    path(
                        '',
                        TeamTasksView.as_view(),
                        name='tasks',
                    ),
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
                'info/',
                include([
                    path(
                        '',
                        InfoCategoriesListView.as_view(),
                        name='info_categories'
                    ),
                    path(
                        '<slug:category_anchor>/', include([
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
                    )
                ])
            ),
            path('shifts/', include([
                path(
                    '',
                    ShiftListView.as_view(),
                    name="shifts"
                ),
                path(
                    'create/',
                    ShiftCreateView.as_view(),
                    name="shift_create"
                ),
                path(
                    'create_multiple/',
                    ShiftCreateMultipleView.as_view(),
                    name="shift_create_multiple"
                ),
                path('<int:pk>/', include([
                    path(
                        '',
                        ShiftUpdateView.as_view(),
                        name="shift_update"
                    ),
                    path(
                        'delete',
                        ShiftDeleteView.as_view(),
                        name="shift_delete"
                    ),
                    path(
                        'take',
                        MemberTakesShift.as_view(),
                        name="shift_member_take"
                    ),
                    path(
                        'drop',
                        MemberDropsShift.as_view(),
                        name="shift_member_drop"
                    ),
                ])),
            ]))
        ]),
    ),
]

