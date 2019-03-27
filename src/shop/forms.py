from django import forms
from django.forms import modelformset_factory

from shop.models import OrderProductRelation


class OrderProductRelationForm(forms.ModelForm):

    class Meta:
        model = OrderProductRelation
        fields = ['quantity']

    def clean_quantity(self):
        product = self.instance.product
        new_quantity = self.cleaned_data['quantity']

        if product.left_in_stock < new_quantity:
            raise forms.ValidationError(
                "Only {} left in stock.".format(
                    product.left_in_stock,
                )
            )

        return new_quantity


OrderProductRelationFormSet = modelformset_factory(
    OrderProductRelation,
    form=OrderProductRelationForm,
    extra=0
)
