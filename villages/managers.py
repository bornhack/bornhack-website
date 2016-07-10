from django.db.models import QuerySet


class VillageQuerySet(QuerySet):

    def not_deleted(self):
        return self.filter(
            deleted=False
        )
