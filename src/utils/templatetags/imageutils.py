from django import template
from django.templatetags.static import static

register = template.Library()


@register.inclusion_tag("thumbnail.html")
def thumbnail(path, filename, description):
    """Returns the HTML to show an image including thumbnail.
    Assumes the thumbnail is called 'thumbnail_foo.jpg.png' if the image is called 'foo.jpg'.
    Path should be relative inside static root.
    Description is used for alt-text and mouseover.
    """
    return {"path": static("") + path, "filename": filename, "description": description}
