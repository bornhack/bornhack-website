import logging
import re
import requests

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.views.generic import View

logger = logging.getLogger("bornhack.%s" % __name__)

class MapProxyView(View):
    """
    Proxy for Datafordeler map service. Created so we can show maps without
    leaking the IP of our visitors.
    """

    PROXY_URL = "/maps/kfproxy"
    VALID_ENDPOINTS = [
        "/GeoDanmarkOrto/orto_foraar_wmts/1.0.0/WMTS",
        "/Dkskaermkort/topo_skaermkort/1.0.0/wms",
        "/DHMNedboer/dhm/1.0.0/wms"
    ]

    def get(self, *args, **kwargs):
        """
        Before we make the request we check that the path is in our whitelist.
        Before we return the response we copy headers except for a list we dont want.
        """

        # Raise PermissionDenied if endpoint isn't valid
        self.is_endpoint_valid(self.request.path)

        # Sanitize the query
        path = self.sanitize_path(self.request.get_full_path())

        # Add credentials to query
        path = self.append_credentials(path)

        # make the request
        r = requests.get("https://services.datafordeler.dk" + path)

        # make the response
        response = HttpResponse(r.content, status=r.status_code)

        # list of headers that cause trouble when proxying
        excluded_headers = [
            "connection",
            "content-encoding",
            "content-length",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
        ]
        # proxy all headers from our upstream request to the response to our client,
        # if the headers are not in our list of troublemakers
        for key, value in r.headers.items():
            if key.lower() not in excluded_headers:
                response[key] = value

        # all good, return the response
        return response

    def is_endpoint_valid(self, path: str) -> None:
        """Validate request path against whitelisted endpoints.
        """
        endpoint = path.replace(self.PROXY_URL, "", 1)
        if endpoint not in self.VALID_ENDPOINTS:
            logger.warning("Maps endpoint was invalid: '%s' valid endpoints: %s",
                           endpoint, self.VALID_ENDPOINTS)
            raise PermissionDenied("No thanks")

    def sanitize_path(self, path: str) -> str:
        """Sanitize path by removing PROXY_URL and set 'transparent' value to upper
        """
        new_path = path.replace(self.PROXY_URL, "", 1)
        sanitized_path = re.sub(
            r"(transparent=)(true|false)",
            lambda match: r"{}{}".format(match.group(1), match.group(2).upper()),
            new_path)
        return sanitized_path

    def append_credentials(self, path: str) -> str:
        """Append & verify credentials is defined in settings or raise exception.
        """
        username = settings.DATAFORDELER_USER
        password = settings.DATAFORDELER_PASSWORD
        if not username or not password:
            logger.error("Missing credentials for "
                         "'DATAFORDELER_USER' or 'DATAFORDELER_PASSWORD'")
            raise Exception("Internal Error")
        path += f"&username={username}&password={password}"
        return path

