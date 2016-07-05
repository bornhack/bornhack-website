from __future__ import unicode_literals

from django.core.urlresolvers import reverse_lazy
from django.db import models
from django.utils.text import slugify

from camps.models import Camp
from utils.models import CreatedUpdatedModel, UUIDModel


class Village(CreatedUpdatedModel, UUIDModel):

    class Meta:
        ordering = ['name']

    camp = models.ForeignKey('camps.Camp')
    contact = models.ForeignKey('auth.User')

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField()

    open = models.BooleanField(
        default=False,
        help_text='Is this village open for others to join?'
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy('villages:detail', kwargs={'slug': self.slug})

    def save(self, **kwargs):
        if (
            not self.pk or
            not self.slug or
            Village.objects.filter(slug=self.slug).count() > 1
        ):
            slug = slugify(self.name)
            incrementer = 1

            # We have to make sure that the slug won't clash with current slugs
            while Village.objects.filter(slug=slug).exists():
                if incrementer == 1:
                    slug = '{}-1'.format(slug)
                else:
                    slug = '{}-{}'.format(
                        '-'.join(slug.split('-')[:-1]),
                        incrementer
                    )
                incrementer += 1
            self.slug = slug

        if not hasattr(self, 'camp'):
            self.camp = Camp.objects.current()

        super(Village, self).save(**kwargs)
