from __future__ import unicode_literals

from django.db import models
from django.utils import encoding
from django.utils.text import slugify

from utils.models import CreatedUpdatedModel
from news.managers import NewsItemQuerySet


@encoding.python_2_unicode_compatible
class NewsItem(CreatedUpdatedModel):
    class Meta:
        ordering = ['-published_at']

    title = models.CharField(max_length=100)
    content = models.TextField()
    public = models.BooleanField(default=False)
    published_at = models.DateTimeField()
    slug = models.SlugField(max_length=255, blank=True)

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        if (
            not self.pk or
            not self.slug or
            NewsItem.objects.filter(slug=self.slug).count() > 1
        ):
            published_at_string = self.published_at.strftime('%Y-%m-%d')
            base_slug = slugify(self.title)
            slug = '{}-{}'.format(published_at_string, base_slug)
            incrementer = 1

            # We have to make sure that the slug won't clash with current slugs
            while NewsItem.objects.filter(slug=slug).exists():
                if incrementer == 1:
                    slug = '{}-1'.format(slug)
                else:
                    slug = '{}-{}'.format(
                        '-'.join(slug.split('-')[:-1]),
                        incrementer
                    )
                incrementer += 1
            self.slug = slug

        super(NewsItem, self).save(**kwargs)

    objects = NewsItemQuerySet.as_manager()
