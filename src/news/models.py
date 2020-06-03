from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from utils.models import CreatedUpdatedModel
from utils.slugs import unique_slugify


class NewsItem(CreatedUpdatedModel):
    class Meta:
        ordering = ["-published_at"]

    title = models.CharField(max_length=100)
    content = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True)
    slug = models.SlugField(max_length=255, blank=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        if self.published_at:
            # if this is a new newsitem, or it doesn't have a slug, or the slug is in use on another item, create a new slug
            if (
                not self.pk
                or not self.slug
                or NewsItem.objects.filter(slug=self.slug).count() > 1
            ):
                published_at_string = self.published_at.strftime("%Y-%m-%d")
                base_slug = slugify(self.title)
                slug = "{}-{}".format(published_at_string, base_slug)
                self.slug = unique_slugify(
                    slug,
                    slugs_in_use=self.__class__.objects.all().values_list(
                        "slug", flat=True
                    ),
                )
        super().save(**kwargs)

    def get_absolute_url(self):
        return reverse("news:detail", kwargs={"slug": self.slug})
