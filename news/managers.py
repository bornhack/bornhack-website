from django.db.models import QuerySet
from django.utils import timezone


class NewsItemQuerySet(QuerySet):

    def public(self):
        return self.filter(
            public=True,
            published_at__lt=timezone.now()
        )
