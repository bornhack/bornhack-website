from __future__ import annotations

from django.urls import path

from . import views

app_name = "news"
urlpatterns = [
    path("", views.NewsIndex.as_view(), kwargs={"archived": False}, name="index"),
    path(
        "archive/",
        views.NewsIndex.as_view(),
        kwargs={"archived": True},
        name="archive",
    ),
    path("feed/", views.NewsFeed(), name="feed"),
    path("<slug:slug>/", views.NewsDetail.as_view(), name="detail"),
]
