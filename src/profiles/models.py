from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from utils.models import CreatedUpdatedModel
from utils.models import UUIDModel


class Profile(ExportModelOperationsMixin("profile"), CreatedUpdatedModel, UUIDModel):
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
        help_text="Your name or handle (only visible to team responsible and organisers)",
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

    @property
    def email(self):
        return self.user.email

    def __str__(self) -> str:
        return self.user.username

    def approve_public_credit_name(self) -> None:
        """This method just sets profile.public_credit_name_approved=True and calls save()
        It is used in an admin action
        """
        self.public_credit_name_approved = True
        self.save()

    @property
    def get_public_credit_name(self):
        """Convenience method to return profile.public_credit_name if it is approved,
        and the string "Unnamed" otherwise
        """
        if self.public_credit_name_approved:
            return self.public_credit_name
        else:
            return "Unnamed"
