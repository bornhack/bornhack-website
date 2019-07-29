import base64
import io

import qrcode
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def qr_code(value):
    stream = io.BytesIO()
    img = qrcode.make("#" + value, box_size=5)
    img.save(stream, "PNG")
    data = base64.b64encode(stream.getvalue())

    return mark_safe(
        "<figure>"
        '<img src="data:image/png;base64,{}" alt="">'
        "<figcaption>{}</figcaption>"
        "</figure>".format(data.decode(), value)
    )
