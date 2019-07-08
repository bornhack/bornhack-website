from django.urls import reverse_lazy
from django.db import models
from django.utils.text import slugify
from utils.models import UUIDModel, CampRelatedModel


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
        if (
            not self.pk
            or not self.slug
            or Village.objects.filter(slug=self.slug).count() > 1
        ):
            slug = slugify(self.name)
            if not slug:
                slug = "noname"
            incrementer = 1

            # We have to make sure that the slug won't clash with current slugs
            while Village.objects.filter(slug=slug).exists():
                if incrementer == 1:
                    slug = "{}-1".format(slug)
                else:
                    slug = "{}-{}".format("-".join(slug.split("-")[:-1]), incrementer)
                incrementer += 1
            self.slug = slug

        super(Village, self).save(**kwargs)

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()
