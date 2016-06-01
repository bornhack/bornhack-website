from django.utils import timezone
from django.db.models import QuerySet


class CampQuerySet(QuerySet):
    def current(self):
        now = timezone.now()
        if self.filter(start__year=now.year).exists():
            return self.get(start__year=now.year)
        return None
