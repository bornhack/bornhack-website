from django import forms

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['payment_method']

