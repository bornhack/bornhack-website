from django.contrib.gis.forms.widgets import BaseGeometryWidget

class OrtoFotoForaarWMTSWidget(BaseGeometryWidget):
    template_name = "mapform.html"
