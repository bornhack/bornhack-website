import logging

from django.contrib.auth.models import User
from colorfield.fields import ColorField
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db.models import GeometryCollectionField
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin
from django.contrib.gis.db.models import PointField

from .utils import LeafletMarkerChoices

from utils.models import CampRelatedModel
from utils.models import UUIDModel
from utils.slugs import unique_slugify

logger = logging.getLogger("bornhack.%s" % __name__)


class Group(UUIDModel):
    """A group of Layers."""

    name = models.CharField(
        max_length=100,
        help_text="Name or description of this group",
    )

    def __str__(self):
        return str(self.name)


class Layer(ExportModelOperationsMixin("layer"), UUIDModel):
    """
    Layers are groups of Features
    """

    name = models.CharField(
        max_length=100,
        help_text="Name or description of this layer",
    )

    slug = models.SlugField(
        blank=True,
        unique=True,
        help_text="The url slug for this layer. Leave blank to autogenerate one.",
    )

    description = models.TextField(help_text="Description of this layer")

    icon = models.CharField(
        max_length=100,
        default="list",
        blank=True,
        help_text="Name of the fontawesome icon to use, including the 'fab fa-' or 'fas fa-' part.",
    )

    invisible = models.BooleanField(
        default=False,
        help_text="Is the layer invisible in the map view?",
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="layers",
    )

    responsible_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        help_text="The Team responsible for this Layer.",
        null=True,
        blank=True,
    )

    @property
    def camp(self):
        return self.responsible_team.camp

    def __str__(self):
        return str(self.name)

    def save(self, **kwargs):
        self.slug = unique_slugify(
            str(self.name),
            slugs_in_use=self.__class__.objects.all().values_list(
                "slug",
                flat=True,
            ),
        )
        super().save(**kwargs)


class Feature(UUIDModel):
    """
    Features are elements to put on a map which can consist of polygons, lines, points, etc.
    """

    name = models.CharField(
        max_length=100,
        help_text="Name or description of this feature",
    )

    description = models.TextField(help_text="Description of this feature")

    geom = GeometryCollectionField(
        help_text="Geometric data",
    )

    color = ColorField(format="hexa", default="#000000FF")

    icon = models.CharField(
        max_length=100,
        default="fab fa-list",
        blank=True,
        help_text="Name of the fontawesome icon to use, including the 'fab fa-' or 'fas fa-' part.",
    )

    url = models.URLField(blank=True)

    topic = models.CharField(
        max_length=200,
        help_text="Name of the topic to update this feature",
        blank=True,
    )

    processing = models.CharField(
        max_length=100,
        help_text="Name of javascript function call for processing data from the topic",
        blank=True,
    )

    layer = models.ForeignKey(
        Layer,
        on_delete=models.CASCADE,
        related_name="features",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["layer", "name"],
                name="layer_and_name_uniq",
            ),
        ]

    def __str__(self):
        return str(self.name)

    @property
    def camp(self):
        return self.layer.team.camp


class ExternalLayer(UUIDModel):
    name = models.CharField(
        max_length=100,
        help_text="Name or description of this layer",
    )

    slug = models.SlugField(
        blank=True,
        unique=True,
        help_text="The url slug for this layer. Leave blank to autogenerate one.",
    )

    description = models.TextField(help_text="Description of this layer")

    url = models.URLField(
        max_length=255,
        help_text="URL of the GEOJSON layer",
    )

    responsible_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        help_text="The Team responsible for this Layer.",
        null=True,
        blank=True,
    )

    @property
    def camp(self):
        return self.responsible_team.camp

    def __str__(self):
        return str(self.name)

    def save(self, **kwargs):
        self.slug = unique_slugify(
            str(self.name),
            slugs_in_use=self.__class__.objects.all().values_list(
                "slug",
                flat=True,
            ),
        )
        super().save(**kwargs)


class UserLocationType(UUIDModel):
    name = models.CharField(
        max_length=100,
        help_text="Name of the user location type",
    )

    slug = models.SlugField(
        blank=True,
        help_text="The url slug for this user location type. Leave blank to autogenerate one.",
    )

    icon = models.CharField(
        max_length=100,
        default="fas fa-list",
        blank=True,
        help_text="Name of the fontawesome icon to use, including the 'fab fa-' or 'fas fa-' part.",
    )

    marker = models.CharField(
        max_length=10,
        choices=LeafletMarkerChoices.choices,
        default=LeafletMarkerChoices.BLUE,
        help_text="The name/colour of the Leaflet marker to use for this facility type.",
    )

    def __str__(self):
        return str(self.name)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.all().values_list(
                    "slug",
                    flat=True,
                ),
            )
        super().save(**kwargs)


class UserLocation(
    UUIDModel,
    CampRelatedModel,
):
    name = models.CharField(
        max_length=100,
        help_text="Name of the location",
    )

    type = models.ForeignKey(
        UserLocationType,
        on_delete=models.CASCADE,
        help_text="Type of this location (extra types can be requested at the GIS team)",
        related_name="user_locations",
    )

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="user_locations",
        on_delete=models.PROTECT,
    )

    user = models.ForeignKey(
        User,
        verbose_name=_("User"),
        help_text=_("The django user this profile belongs to."),
        on_delete=models.PROTECT,
    )

    location = PointField(
        blank=True,
        null=True,
        help_text="Location of this location.",
    )

    data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return str(self.name)
