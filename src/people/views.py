from camps.models import Camp
from django.views.generic import ListView


class PeopleView(ListView):
    template_name = "people.html"
    model = Camp
