from django import forms


class AddToOrderForm(forms.Form):
    quantity = forms.IntegerField(initial=1)

