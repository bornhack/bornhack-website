import hashlib, hmac

class CoinifyCallback:
    """
    Class to validate callbacks from Coinfy
    """

    ipn_secret = None
    """Coinify IPN callback secret. Get yours at https://www.coinify.com/merchant/ipn"""

    def __init__( self, ipn_secret ):
        self.ipn_secret = ipn_secret

    def validate_callback( self, callback_raw, signature ):
        """
        Validates a callback and it's signature based on the IPN secret given in the constructor.

        callback_raw must contain the raw JSON POST data sent with the callback (before any JSON decoding)
        signature must contain the signature as extracted from the 'X-Coinify-Callback-Signature' header,
            which should be a 64-byte hexadecimal string
        """
        return signature == hmac.new(self.ipn_secret, msg=callback_raw, digestmod=hashlib.sha256).hexdigest()

