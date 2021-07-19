import logging
import uuid

from django.contrib import messages
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase

logger = logging.getLogger("bornhack.%s" % __name__)


class CleanedModel(models.Model):
    class Meta:
        abstract = True

    def save(self, **kwargs):
        try:
            # call this models full_clean() method before saving,
            # which in turn calls .clean_fields(), .clean() and .validate_unique()
            # self.full_clean()
            # for some reason self.full_clean() appears to call self.clean() before self.clean_fields()
            # which is not supposed to happen. Call them manually one by one instead.
            self.clean_fields()
            self.clean()
            self.validate_unique(exclude=None)
        except ValidationError as e:
            message = "Got ValidationError while saving: %s" % e
            if hasattr(self, "request"):
                messages.error(self.request, message)
            logger.error(message)
            # dont save, re-raise the exception
            raise
        super().save(**kwargs)


class UUIDModel(CleanedModel):
    class Meta:
        abstract = True

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class CreatedUpdatedModel(CleanedModel):
    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class CampReadOnlyModeError(ValidationError):
    pass


class CampRelatedModel(CreatedUpdatedModel):

    camp_filter = "camp"

    class Meta:
        abstract = True

    def save(self, **kwargs):
        if self.camp.read_only:
            if hasattr(self, "request"):
                messages.error(self.request, f"Camp {self.camp} is in read only mode.")
            raise CampReadOnlyModeError(f"The camp {self.camp} is in read only mode.")

        super().save(**kwargs)

    def delete(self, **kwargs):
        if self.camp.read_only:
            if hasattr(self, "request"):
                messages.error(self.request, "Camp is in read only mode.")
            raise CampReadOnlyModeError("This camp is in read only mode.")

        super().delete(**kwargs)

    @classmethod
    def get_camp_filter(cls):
        return cls.camp_filter


class OutgoingEmail(CreatedUpdatedModel):
    """The OutgoingEmail model contains all system emails, both unsent and sent."""

    subject = models.CharField(max_length=500, help_text="The subject of the e-mail")
    text_template = models.TextField(help_text="The plaintext body of the email.")
    html_template = models.TextField(
        blank=True, help_text="The HTML body of the email (optional)."
    )
    sender = models.CharField(max_length=500, help_text="The email sender.")
    to_recipients = ArrayField(
        models.CharField(max_length=500, blank=True),
        null=True,
        blank=True,
        help_text="The To: recipients",
    )
    cc_recipients = ArrayField(
        models.CharField(max_length=500, blank=True),
        null=True,
        blank=True,
        help_text="The Cc: recipients",
    )
    bcc_recipients = ArrayField(
        models.CharField(max_length=500, blank=True),
        null=True,
        blank=True,
        help_text="The Bcc: recipients",
    )
    attachment = models.FileField(
        blank=True, help_text="The attachment for this email. Optional."
    )
    processed = models.BooleanField(
        default=False,
        help_text="Unchecked before the email is sent, checked after the email has been sent.",
    )
    hold = models.BooleanField(
        default=False, help_text="Hold (do not send) this email. Uncheck to send."
    )
    responsible_team = models.ForeignKey(
        "teams.Team",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        help_text="The Team responsible for this email.",
    )

    def __str__(self):
        return "OutgoingEmail Object id: {} ".format(self.id)

    def clean(self):
        if (
            not self.to_recipients
            and not self.bcc_recipients
            and not self.cc_recipients
        ):
            raise ValidationError(
                {
                    "recipient": "either to_recipient, bcc_recipient or cc_recipient required."
                }
            )


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    """Allows us to tag models with a UUID pk, use with TaggableManager(through=UUIDTaggedItem)"""

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
