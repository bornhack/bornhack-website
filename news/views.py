from django.views.generic import ListView
from . import models


class NewsIndex(ListView):
    model = models.NewsItem
    queryset = models.NewsItem.objects.public()
    template_name = 'news_index.html'
    context_object_name = 'news_items'
