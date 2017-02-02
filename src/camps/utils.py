from camps.models import Camp
from django.utils import timezone

def get_current_camp():
    try:
        return Camp.objects.get(camp__contains=timezone.now())
    except Camp.DoesNotExist:
        return False

