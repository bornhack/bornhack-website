from django.conf.urls import url
from .views import *

urlpatterns = [
    url(
        r'^$',
        TeamListView.as_view(),
        name='list'
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
        r'(?P<team_slug>[-_\w+]+)/tasks/(?P<slug>[-_\w+]+)/$',
        TaskDetailView.as_view(),
        name='task_detail',
    ),
    url(
        r'(?P<slug>[-_\w+]+)/join/$',
        TeamJoinView.as_view(),
        name='join'
    ),
    url(
        r'(?P<slug>[-_\w+]+)/leave/$',
        TeamLeaveView.as_view(),
        name='leave'
    ),
    url(
        r'(?P<slug>[-_\w+]+)/manage/$',
        TeamManageView.as_view(),
        name='manage'
    ),
    # this has to be the last url in the list
    url(
        r'(?P<slug>[-_\w+]+)/$',
        TeamDetailView.as_view(),
        name='detail'
    ),
]

