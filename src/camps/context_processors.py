"""Add current camp and camps list to template context.

This is done here and not in CampViewMixin because most views need the camp and camps
list in tempalte context but not all views need queryset filtering by camp.
"""

from .models import Camp


def camp(request):
    """If we have a camp in the request object (added by RequestCampMiddleware based on
    the camp_slug url kwarg) add it to the context.
    Also add a "camps" queryset containing all camps (used to build the menu and such)
    """
    camp = None
    if hasattr(request, "camp"):
        camp = request.camp
    return {"camps": Camp.objects.all().order_by("-camp"), "camp": camp}
