from psycopg2.extras import DateTimeTZRange

from django.db.models import QuerySet
from django.utils import timezone


class TicketTypeQuerySet(QuerySet):

    def available(self):
        now = timezone.now()
        return self.filter(
            available_in__contains=DateTimeTZRange(now, None)
        )
