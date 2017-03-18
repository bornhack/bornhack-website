import uuid
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import models


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
            self.validate_unique()
        except ValidationError as e:
            message = "Got ValidationError while saving: %s" % e
            if hasattr(self, 'request'):
                messages.error(self.request, message)
            print(message)
            # dont save, re-raise the exception
            raise
        super(CleanedModel, self).save(**kwargs)


class UUIDModel(CleanedModel):
    class Meta:
        abstract = True

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )


class CreatedUpdatedModel(CleanedModel):
    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class CampRelatedModel(CreatedUpdatedModel):
    class Meta:
        abstract = True

    def save(self, **kwargs):
        if self.camp.read_only:
            if hasattr(self, 'request'):
                messages.error(self.request, 'Camp is in read only mode.')
            raise ValidationError('This camp is in read only mode.')

        super().save(**kwargs)

    def delete(self, **kwargs):
        if self.camp.read_only:
            if hasattr(self, 'request'):
                messages.error(self.request, 'Camp is in read only mode.')
            raise ValidationError('This camp is in read only mode.')

        super().delete(**kwargs)
