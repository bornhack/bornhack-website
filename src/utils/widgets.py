from django.forms import Widget


class IconPickerWidget(Widget):
    template_name = 'icon_picker_widget.html'

    class Media:
        js = ("/static/modules/universal-icon-picker/assets/js/universal-icon-picker.min.js",)

    def format_value(self, value):
        if value is None:
            return ''
        return value

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['id'] = name
        context['widget']['value'] = self.format_value(value)
        context['widget']['disabled'] = True
        return context
