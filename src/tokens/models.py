from django.db import models
from utils.models import CampRelatedModel


class Token(CampRelatedModel):
    camp = models.ForeignKey(
        'camps.Camp',
        on_delete=models.PROTECT
    )

    token = models.CharField(
        max_length=32,
        help_text="The secret token"
    )

    description = models.TextField(
        help_text="The description of the token"
    )

    camp_filter = 'camp'

    def __str__(self):
        return '%s (%s)' % (self.description, self.camp)


class TokenFind(CampRelatedModel):
    token = models.ForeignKey(
        'tokens.Token',
        on_delete=models.PROTECT
    )

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
    )

    camp_filter = 'token__camp'

    def __str__(self):
        return '%s found by %s' % (self.token, self.user)

    @property
    def camp(self):
        return self.token.camp

