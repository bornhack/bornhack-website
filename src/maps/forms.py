from django.contrib.gis import forms
from .widgets import OrtoFotoForaarWMTSWidget

class MyGeoForm(forms.Form):
    geometry = forms.GeometryCollectionField(widget=OrtoFotoForaarWMTSWidget(attrs={'map_width': 800, 'map_height': 500}))
