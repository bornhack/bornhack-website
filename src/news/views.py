from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import NewsItem


class NewsIndex(ListView):
    model = NewsItem
    template_name = 'news_index.html'
    context_object_name = 'news_items'

    def get_queryset(self):
        return NewsItem.objects.filter(
            published_at__isnull=False,
            published_at__lt=timezone.now(),
            archived=self.kwargs['archived']
        )


class NewsDetail(DetailView):
    model = NewsItem
    template_name = 'news_detail.html'
    context_object_name = 'news_item'

