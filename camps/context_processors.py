from django.conf import settings
from .models import Camp
from django.utils import timezone


def camps(request):
    return {
        'upcoming_camps': Camp.objects.filter(camp_start__gt=timezone.now()),
        'previous_camps': Camp.objects.filter(camp_start__lt=timezone.now()),
    }

