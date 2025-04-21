from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.gis.db.models import PointField

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

    # default to near general camping
    location = PointField(
        blank=True,
        null=True,
        help_text="Your location at BornHack. This value is available on public maps.",
    )

    @property
    def email(self):
        return self.user.email

    def __str__(self):
        return self.user.username

    def approve_public_credit_name(self):
        """
        This method just sets profile.public_credit_name_approved=True and calls save()
        It is used in an admin action
        """
        self.public_credit_name_approved = True
        self.save()

    @property
    def get_public_credit_name(self):
        """
        Convenience method to return profile.public_credit_name if it is approved,
        and the string "Unnamed" otherwise
        """
        if self.public_credit_name_approved:
            return self.public_credit_name
        else:
            return "Unnamed"
