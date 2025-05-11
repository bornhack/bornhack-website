import base64
import io

import qrcode
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def qr_code(value):
    stream = io.BytesIO()
    img = qrcode.make(value, box_size=7)
    img.save(stream, "PNG")
    data = base64.b64encode(stream.getvalue())

    return mark_safe(
        "<figure style='text-align: center;'>"
        f"<figcaption style='text-align: center;'>{value}</figcaption>"
        f'<img src="data:image/png;base64,{data.decode()}" alt="">'
        "</figure>",
    )
