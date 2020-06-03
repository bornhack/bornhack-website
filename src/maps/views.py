import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.views.generic import View


class MapProxyView(View):
    """
    Proxy for KortForsyningen map service. Created so we can show maps without
    leaking the IP of our visitors.
    """

    def get(self, *args, **kwargs):
        """
        Before we make the request we check that the path is in our whitelist.
        Before we return the response we copy headers except for a list we dont want.
        """
        # only permit certain paths
        path = self.request.path.replace("/maps/kfproxy", "", 1)
        if path not in ["/orto_foraar", "/topo_skaermkort", "/mat", "/dhm"]:
            raise PermissionDenied("No thanks")

        # ok, get the full path including querystring, and add our token
        fullpath = self.request.get_full_path().replace("/maps/kfproxy", "", 1)
        fullpath += f"&token={settings.KORTFORSYNINGEN_TOKEN}"

        # make the request
        r = requests.get("https://services.kortforsyningen.dk" + fullpath)

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
