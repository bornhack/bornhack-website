from __future__ import annotations

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CreatedUpdatedModel
from utils.models import UUIDModel
from economy.models import Expense
from economy.models import Revenue


class Profile(ExportModelOperationsMixin("profile"), CreatedUpdatedModel, UUIDModel):
    THEME_CHOICES = (
        ("default", "Default (Auto)"),
        ("light", "Light"),
        ("slate", "Slate"),
        ("solar", "Solar"),
    )

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    user = models.OneToOneField(
        User,
        verbose_name=_("User"),
        help_text=_("The django user this profile belongs to."),
        on_delete=models.PROTECT,
    )

    name = models.CharField(
        max_length=200,
        default="",
        blank=True,
        help_text="Your name or handle (only visible to team leads and orga)",
    )

    description = models.TextField(
        default="",
        blank=True,
        help_text="Please include any info you think could be relevant, like drivers license, first aid certificates, crafts, skills and previous experience. Please also include availability if you are not there for the full week.",
    )

    public_credit_name = models.CharField(
        blank=True,
        max_length=100,
        help_text="The name you want to appear on in the credits section of the public website (on Team and People pages). Leave this empty if you want your name hidden on the public webpages.",
    )

    public_credit_name_approved = models.BooleanField(
        default=False,
        help_text="Check this box to approve this users public_credit_name. This will be unchecked automatically when the user edits public_credit_name",
    )

    nickserv_username = models.CharField(
        blank=True,
        max_length=50,
        help_text="Your NickServ username is used to manage team IRC channel access lists. Make sure you register with NickServ _before_ you enter the username here!",
    )

    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default="default")

    phonenumber = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(9999)],
        help_text="The phonenumber you can be reached on. This field can be updated automatically when registering a DECT number in the phonebook.",
    )

    preferred_username = models.SlugField(
        blank=True,
        max_length=50,
        help_text="When using your BornHack account to login to other sites with OIDC this value is served as the OIDC standard claim 'preferred_username'. You can set this to the username you would prefer to use on remote sites where you login with your BornHack account.",
    )

    @property
    def email(self):
        return self.user.email

    def __str__(self) -> str:
        return self.user.username

    def approve_public_credit_name(self) -> None:
        """This method just sets profile.public_credit_name_approved=True and calls save()
        It is used in an admin action.
        """
        self.public_credit_name_approved = True
        self.save()

    @property
    def get_public_credit_name(self):
        """Convenience method to return profile.public_credit_name if it is approved,
        and the string "Unnamed" otherwise.
        """
        if self.public_credit_name_approved:
            return self.public_credit_name
        return "Unnamed"

    @property
    def get_name(self):
        """Convenience method to return profile.name if set, otherwise username."""
        if self.name:
            return self.name
        return self.user.username

    @property
    def paid_expenses_needs_reimbursement(self):
        """The paid_expense_needs_reimbursement property."""
        return Expense.objects.filter(
            user=self.user,
            approved=True,
            reimbursement__isnull=True,
            payment_status="PAID_NEEDS_REIMBURSEMENT",
        )

    @property
    def paid_revenues_needs_redisbursement(self):
        """The paid_revenues_needs_redisbursement property."""
        return Revenue.objects.filter(
            user=self.user,
            approved=True,
            reimbursement__isnull=True,
            payment_status="PAID_NEEDS_REDISBURSEMENT",
        )

