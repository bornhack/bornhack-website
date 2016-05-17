import requests, json, time, hashlib, hmac


class CoinifyAPI:
    api_key = None
    """Coinify API key. Get yours at https://www.coinify.com/merchant/api"""

    api_secret = None
    """Coinify API secret. Get yours at https://www.coinify.com/merchant/api"""

    api_base_url = None
    """Base URL to the Coinify API"""

    API_DEFAULT_BASE_URL = "https://api.coinify.com"

    def __init__(self, api_key=None, api_secret=None, api_base_url=None):
        """
        Create an instance of the CoinifyAPI class.
        Provide your API key and API secret.

        Set api_base_url to None to use default
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_base_url = api_base_url or self.API_DEFAULT_BASE_URL

    def invoices_list(self, limit=None, offset=None, include_expired=None):
        """
        Returns an array of your Coinify invoices

        See https://www.coinify.com/docs/api/#list-all-invoices
        """
        query_params = {}

        if limit is not None:
            query_params['limit'] = limit
        if offset is not None:
            query_params['offset'] = offset
        if include_expired is not None:
            query_params['include_expired'] = include_expired

        return self.call_api_authenticated('/v3/invoices', query_params=query_params)

    def invoice_create(self, amount, currency, plugin_name, plugin_version,
                       description=None, custom=None, callback_url=None, callback_email=None,
                       return_url=None, cancel_url=None, input_currency=None, input_return_address=None):

        """
        Create a new invoice.

        See https://www.coinify.com/docs/api/#create-an-invoice
        """
        params = {
            'amount': amount,
            'currency': currency,
            'plugin_name': plugin_name,
            'plugin_version': plugin_version
        }

        if description is not None:
            params['description'] = description
        if custom is not None:
            params['custom'] = custom
        if callback_url is not None:
            params['callback_url'] = callback_url
        if callback_email is not None:
            params['callback_email'] = callback_email
        if return_url is not None:
            params['return_url'] = return_url
        if cancel_url is not None:
            params['cancel_url'] = cancel_url
        if input_currency is not None:
            params['input_currency'] = input_currency
        if input_return_address is not None:
            params['input_return_address'] = input_return_address

        return self.call_api_authenticated('/v3/invoices', 'POST', params)

    def invoice_get(self, invoice_id):
        """
        Get a specific invoice

        See https://www.coinify.com/docs/api/#get-a-specific-invoice
        """
        path = '/v3/invoices/%d' % (invoice_id,)

        return self.call_api_authenticated(path)

    def invoice_update(self, invoice_id, description=None, custom=None):
        """
        Update the description and custom data of an invoice

        See https://www.coinify.com/docs/api/#update-an-invoice
        """
        params = {}

        if description is not None:
            params['description'] = description
        if custom is not None:
            params['custom'] = custom

        path = '/v3/invoices/%d' % (invoice_id,)

        return self.call_api_authenticated(path, 'PUT', params)

    def invoice_input_create(self, invoice_id, currency, return_address):
        """
        Request for an invoice to be paid with another input currency.

        See https://www.coinify.com/docs/api/#pay-with-another-input-currency
        """
        params = {
            'currency': currency,
            'return_address': return_address
        }

        path = '/v3/invoices/%d/inputs' % (invoice_id,)

        return self.call_api_authenticated(path, 'POST', params)

    def buy_orders_list(self, limit=None, offset=None, include_cancelled=None):
        """
        Returns an array of your Coinify buy orders

        See https://www.coinify.com/docs/api/#list-all-buy-orders
        """

        query_params = {}

        if limit is not None:
            query_params['limit'] = limit
        if offset is not None:
            query_params['offset'] = offset
        if include_cancelled is not None:
            query_params['include_cancelled'] = include_cancelled

        return self.call_api_authenticated('/v3/buys', query_params=query_params)

    def buy_order_create(self, amount, currency, btc_address, instant_order=None,
                         callback_url=None, callback_email=None):
        """
        Create a new buy order

        See https://www.coinify.com/docs/api/#create-a-buy-order
        """
        params = {
            'amount': amount,
            'currency': currency,
            'btc_address': btc_address
        }

        if instant_order is not None:
            params['instant_order'] = instant_order
        if callback_url is not None:
            params['callback_url'] = callback_url
        if callback_email is not None:
            params['callback_email'] = callback_email

        return self.call_api_authenticated('/v3/buys', 'POST', params)

    def buy_order_confirm(self, buy_order_id):
        """
        Confirm a buy order

        See https://www.coinify.com/docs/api/#buy-order-confirm
        """
        path = '/v3/buys/%d/actions/confirm' % (buy_order_id,)

        return self.call_api_authenticated(path, 'PUT')

    def buy_order_get(self, buy_order_id):
        """
        Get a specific buy order

        See https://www.coinify.com/docs/api/#get-a-specific-buy-order
        """
        path = '/v3/buys/%d' % (buy_order_id,)

        return self.call_api_authenticated(path)

    def rates_get(self, currency=None):
        """
        Return buy and sell rates for all available currencies or for the specified currency.
        :param self:
        :param currency|None: A 3-char currency code
        :return:
        """
        if currency is None:
            path = '/v3/rates'
        else:
            path = '/v3/rates/%s' % (currency,)

        return self.call_api_authenticated(path)

    def balance_get(self):
        """
        Get the balance of a merchant
        :param path:
        :return: An array as described in https://www.coinify.com/docs/api/#check-account-balance . If success,
                then the 'data' value contains the balance in BTC and fiat currency and also the base currency
                of the merchant that requests it.
        """
        path = '/v3/balance'
        return self.call_api_authenticated(path)

    def input_currencies_list(self):
        """
        Receive a list of supported input currencies
        """

        return self.call_api('/v3/input-currencies')

    def call_api_authenticated(self, path, method='GET', params={}, query_params={}):
        """
        Perform an authenticated API call, using the
        API key and secret provided in the constructor.

        path: API path, WITH a leading slash, e.g. '/v3/invoices'
        params: dict with parameters to send with the API call

        Returns a dict as described in https://www.coinify.com/docs/api/#response-format,
        or None if the HTTP call couldn't be performed correctly.
        """
        extra_headers = {
            'Authorization': self.generate_authorization_header()
        }

        return self.call_api(path, method, params, query_params, extra_headers)

    def call_api(self, path, method='GET', params={}, query_params={}, headers={}):
        """
        Perform an API call

        path: API path, WITH a leading slash, e.g. '/v3/invoices'
        params: dict with parameters to send with the API call

        Returns a dict as described in https://www.coinify.com/docs/api/#response-format,
        or None if the HTTP call couldn't be performed correctly.
        """
        url = self.api_base_url + path

        headers['Content-Type'] = 'application/json'

        if self.api_key is not None:
            headers['Authorization'] = self.generate_authorization_header()

        r = requests.request(method, url, json=params, headers=headers, params=query_params)
        return r.json()

    def generate_authorization_header(self):
        """
        Generate a nonce and a signature for an API call
        and wrap those in a HTTP header
        """
        # Generate nonce, based on the current Unix timestamp
        nonce = str(int(time.time() * 1000000))

        # Concatenate nonce and API key
        message = nonce + self.api_key

        # Compute signature
        signature = hmac.new(self.api_secret, msg=message, digestmod=hashlib.sha256).hexdigest()

        # Construct the header value
        header_value = 'Coinify apikey="%s", nonce="%s", signature="%s"' % (self.api_key, nonce, signature)

        return header_value

