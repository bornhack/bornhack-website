from .models import Camp


def current_camp(request):
    return {'current_camp': Camp.objects.current()}
