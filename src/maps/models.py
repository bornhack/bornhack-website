from django_prometheus.models import ExportModelOperationsMixin
from utils.models import UUIDModel, CampRelatedModel
from django.contrib.gis.db.models import GeometryCollectionField
from django.db import models
from polymorphic.models import PolymorphicModel


class Geometry(ExportModelOperationsMixin("geometry"), UUIDModel, PolymorphicModel):
    """The Geometry model contains all geometries for our GIS stuff."""

    responsible_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        help_text="The Team responsible for this geometry.",
    )

    geometry = GeometryCollectionField(help_text="The collection of geometries for this object.")

    name = models.CharField(max_length=100, help_text="The name of this geometry collection.")

    description = models.TextField(help_text="Description of this geometry collection.")


class FacilityGeometry(ExportModelOperationsMixin("facility_geometry"), CampRelatedModel, Geometry):
    """This model contains all Geometry objects for Facilities."""
    facility = models.ForeignKey(
        "facilities.Facility",
        related_name="geometries",
        on_delete=models.PROTECT,
        help_text="The Facility to which this geometry belongs",
    )

    camp_filter =  "facility__facility_type__responsible_team__camp"


class VillageGeometry(ExportModelOperationsMixin("village_geometry"), CampRelatedModel, Geometry):
    """This model contains all Geometry objects for Villages."""
    village = models.ForeignKey(
        "villages.Village",
        related_name="geometries",
        on_delete=models.PROTECT,
        help_text="The Village to which this geometry belongs",
    )

    camp_filter =  "village__camp"
