from __future__ import annotations

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CreatedUpdatedModel
from utils.slugs import unique_slugify


class NewsItem(ExportModelOperationsMixin("news_item"), CreatedUpdatedModel):
    class Meta:
        ordering = ["-published_at"]

    title = models.CharField(max_length=100)
    content = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True)
    slug = models.SlugField(max_length=255, blank=True)
    archived = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title

    def save(self, **kwargs) -> None:
        if self.published_at:
            # if this is a new newsitem, or it doesn't have a slug, or the slug is in use on another item, create a new slug
            if not self.pk or not self.slug or NewsItem.objects.filter(slug=self.slug).count() > 1:
                published_at_string = self.published_at.strftime("%Y-%m-%d")
                base_slug = slugify(self.title)
                slug = f"{published_at_string}-{base_slug}"
                self.slug = unique_slugify(
                    slug,
                    slugs_in_use=self.__class__.objects.all().values_list(
                        "slug",
                        flat=True,
                    ),
                )
        super().save(**kwargs)

    def get_absolute_url(self):
        return reverse("news:detail", kwargs={"slug": self.slug})
