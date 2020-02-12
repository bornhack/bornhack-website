import logging
import uuid

from django.contrib import messages
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models

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
        super(CleanedModel, self).save(**kwargs)


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
                messages.error(self.request, "Camp is in read only mode.")
            raise CampReadOnlyModeError("This camp is in read only mode.")

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
    subject = models.CharField(max_length=500)
    text_template = models.TextField()
    html_template = models.TextField(blank=True)
    sender = models.CharField(max_length=500)
    to_recipients = ArrayField(
        models.CharField(max_length=500, blank=True), null=True, blank=True
    )
    cc_recipients = ArrayField(
        models.CharField(max_length=500, blank=True), null=True, blank=True
    )
    bcc_recipients = ArrayField(
        models.CharField(max_length=500, blank=True), null=True, blank=True
    )
    attachment = models.FileField(blank=True)
    processed = models.BooleanField(default=False)

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
