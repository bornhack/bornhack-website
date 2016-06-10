from django.views.generic import ListView, DetailView
from django.utils import timezone
from . import models


class NewsIndex(ListView):
    model = models.NewsItem
    queryset = models.NewsItem.objects.public()
    template_name = 'news_index.html'
    context_object_name = 'news_items'


class NewsDetail(DetailView):
    model = models.NewsItem
    template_name = 'news_detail.html'
    context_object_name = 'news_item'

    def get_context_data(self, **kwargs):
        context = super(NewsDetail, self).get_context_data(**kwargs)
        news_item = self.get_object()
        context['draft'] = False
        if news_item.public and news_item.published_at > timezone.now():
            context['draft'] = True
        return context

