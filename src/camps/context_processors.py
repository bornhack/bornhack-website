from .models import Camp


def camp(request):
    """
    If we have a camp in the request object add it to request.session and context.
    Also add a "camps" queryset containing all camps (used to build the menu and such)
    """
    if hasattr(request, "camp"):
        camp = request.camp
        request.session["campslug"] = camp.slug
    else:
        request.session["campslug"] = None
        camp = None
    return {"camps": Camp.objects.all().order_by("-camp"), "camp": camp}
