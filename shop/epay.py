import hashlib
from django.conf import settings

def calculate_epay_hash(order, request):
    hashstring = (
        '{merchant_number}{description}11{amount}DKK'
        '{order_id}{accept_url}{cancel_url}{md5_secret}'
    ).format(
        merchant_number=settings.EPAY_MERCHANT_NUMBER,
        description=order.description,
        amount=order.total*100,
        order_id=order.pk,
        accept_url = order.get_epay_accept_url(request),
        cancel_url = order.get_cancel_url(request),
        md5_secret=settings.EPAY_MD5_SECRET,
    )
    epay_hash = hashlib.md5(hashstring).hexdigest()
    return epay_hash


def validate_epay_callback(query):
    hashstring = ''
    for key, value in query.iteritems():
        if key != 'hash':
            hashstring += value
    hash = hashlib.md5(hashstring + settings.EPAY_MD5_SECRET).hexdigest()
    return hash == query['hash']

