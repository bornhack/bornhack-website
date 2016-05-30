from __future__ import unicode_literals

from django.db import models

from utils.models import CreatedUpdatedModel
from news.managers import NewsItemQuerySet


class NewsItem(CreatedUpdatedModel):
    class Meta:
        ordering = ['-published_at']

    title = models.CharField(max_length=100)
    content = models.TextField()
    public = models.BooleanField(default=False)
    published_at = models.DateTimeField()

    def __str__(self):
        return self.title

    objects = NewsItemQuerySet.as_manager()
