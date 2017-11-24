import os

from django.conf import settings
from django.views.generic.detail import SingleObjectMixin
from sendfile import sendfile


class FileViewMixin(SingleObjectMixin):
    file_field = None
    file_directory_name = None
    object_id_field = None

    def get_directory_name(self):
        return self.file_directory_name

    def get_identifier(self):
        return getattr(self.get_object(), self.object_id_field)

    def get_filename(self):
        file_field = getattr(
            self.get_object(),
            self.file_field
        )
        return os.path.basename(file_field.name)

    def get_path(self):
        return '/public/{directory_name}/{camp_slug}/{identifier}/{filename}'.format(
            directory_name=self.get_directory_name(),
            camp_slug=self.camp.slug,
            identifier=self.get_identifier(),
            filename=self.get_filename()
        )

    def get(self, request, *args, **kwargs):
        path = '{media_root}{file_path}'.format(
            media_root=settings.MEDIA_ROOT,
            file_path=self.get_path()
        )
        return sendfile(request, path)