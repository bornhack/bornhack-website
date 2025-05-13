"""Utils for the Maps APP."""
from __future__ import annotations

from django.db import models


class LeafletMarkerChoices(models.TextChoices):
    """Leaflet icon color choices.

    a models.TextChoices class to use when we want to set
    choices for a model field to pick a marker colour for a Leaflet map.
    These map directly to the L.Icon() objects in static_src/js/leaflet-color-markers.js.
    """

    BLUE = "blueIcon", "Blue (#2A81CB)"
    GOLD = "goldIcon", "Gold (#FFD326)"
    RED = "redIcon", "Red (#CB2B3E)"
    GREEN = "greenIcon", "Green (#2AAD27)"
    ORANGE = "orangeIcon", "Orange (#CB8427)"
    YELLOW = "yellowIcon", "Yellow (#CAC428)"
    VIOLET = "violetIcon", "Violet (#9C2BCB)"
    GREY = "greyIcon", "Grey (#7B7B7B)"
    BLACK = "blackIcon", "Black (#3D3D3D)"
