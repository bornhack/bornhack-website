from __future__ import annotations

from django.contrib.syndication.views import Feed
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic import ListView

from .models import NewsItem


def news_items_queryset(kwargs=None):
    archived = False if not kwargs else kwargs["archived"]

    return NewsItem.objects.filter(
        published_at__isnull=False,
        published_at__lt=timezone.now(),
        archived=archived,
    )


class NewsIndex(ListView):
    model = NewsItem
    template_name = "news_index.html"
    context_object_name = "news_items"

    def get_queryset(self):
        return news_items_queryset(self.kwargs)


class NewsDetail(DetailView):
    model = NewsItem
    template_name = "news_detail.html"
    context_object_name = "news_item"


class NewsFeed(Feed):
    title = "BornHack News"
    link = "/news"

    def items(self):
        return news_items_queryset()

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content
