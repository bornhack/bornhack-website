from django.shortcuts import get_object_or_404


class RequestCampMiddleware:
    """Add camp as an attribute on the request object."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        from camps.models import Camp

        if (
            hasattr(request, "resolver_match")
            and request.resolver_match
            and "camp_slug" in request.resolver_match.kwargs
        ):
            camp = get_object_or_404(Camp, slug=view_kwargs["camp_slug"])
            request.camp = camp
