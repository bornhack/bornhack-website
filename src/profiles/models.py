from __future__ import annotations

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from economy.models import Expense
from economy.models import Revenue
from camps.models import Camp
from teams.models import TeamMember
from utils.models import CreatedUpdatedModel
from utils.models import UUIDModel


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
        help_text="What can we call you? (visible to any team member aka. volunteer, but not the public)",
    )

    description = models.TextField(
        default="",
        blank=True,
        help_text="Please include any info you think could be relevant, like drivers license, first aid certificates, crafts, skills and previous experience. Please also include availability if you are not there for the full week.",
    )

    public_credit_name = models.CharField(
        blank=True,
        max_length=100,
        help_text="The name you want to appear in the credits section of the public website (on Team and People pages). Leave this empty if you want your name hidden on the public webpages.",
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

    def __str__(self) -> str:
        return self.user.username

    def approve_public_credit_name(self) -> None:
        """This method just sets profile.public_credit_name_approved=True
        and calls save(). It is used in an admin action.
        """
        self.public_credit_name_approved = True
        self.save()

    @property
    def email(self):
        return self.user.email

    def get_display_name(self, user: User, camp: Camp) -> str:
        """
        Return the profile's public or private name depending on
        requesting user's team membership.

        `private_name` is returned for all volunteers, defined as someone who is
        a team member in the relevant camp.

        `public_name` is unrestricted and returned in all other cases.
        """
        if not user.is_authenticated:
            return self.public_name

        if TeamMember.objects.filter(user=user, team__camp=camp).exists():
            return self.private_name

        return self.public_name

    @property
    def paid_expenses_needs_reimbursement(self) -> models.QuerySet:
        """The paid_expense_needs_reimbursement property."""
        return Expense.objects.filter(
            user=self.user,
            approved=True,
            reimbursement__isnull=True,
            payment_status="PAID_NEEDS_REIMBURSEMENT",
        )

    @property
    def paid_revenues_needs_redisbursement(self) -> models.QuerySet:
        """The paid_revenues_needs_redisbursement property."""
        return Revenue.objects.filter(
            user=self.user,
            approved=True,
            reimbursement__isnull=True,
            payment_status="PAID_NEEDS_REDISBURSEMENT",
        )

    @property
    def public_name(self) -> str:
        """Return `public_credit_name` if it is approved or else `Unnamed`.

        Unrestricted usage.
        """
        return (
            self.public_credit_name
            if self.public_credit_name_approved
            else "Unnamed"
        )

    @property
    def private_name(self) -> str:
        """Return `name` if set or else `public_credit_name` if approved,
        with fallback to username.

        Restricted usage: Should only be visible to team members for related camp.
        """
        if self.name:
            return self.name
        elif self.public_credit_name_approved:
            return self.public_credit_name
        else:
            return self.user.username

