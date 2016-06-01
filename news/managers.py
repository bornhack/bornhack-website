from django.db.models import QuerySet


class NewsItemQuerySet(QuerySet):

    def public(self):
        return self.filter(
            public=True
        )
