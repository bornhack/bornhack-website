from django.db import models
from django.urls import reverse_lazy
from utils.models import CampRelatedModel, UUIDModel
from utils.slugs import unique_slugify


class Village(UUIDModel, CampRelatedModel):
    class Meta:
        ordering = ["name"]
        unique_together = ("slug", "camp")

    contact = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    camp = models.ForeignKey("camps.Camp", on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(
        help_text="A descriptive text about your village. Markdown is supported."
    )

    private = models.BooleanField(
        default=False,
        help_text="Check if your village is invite only. Leave unchecked to welcome strangers.",
    )

    deleted = models.BooleanField(default=False)

    def __str__(self):
        return "%s (%s)" % (self.name, self.camp.title)

    def get_absolute_url(self):
        return reverse_lazy(
            "village_detail", kwargs={"camp_slug": self.camp.slug, "slug": self.slug}
        )

    def save(self, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.filter(camp=self.camp).values_list(
                    "slug", flat=True
                ),
            )
        super().save(**kwargs)

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
