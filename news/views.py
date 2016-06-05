from django.views.generic import ListView, DetailView
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

