from django import forms
from .models import Order


class CheckoutForm(forms.Form):
    # no fields here, just three submit buttons
    pass

