from django.forms import Textarea
from django.forms import TextInput
from django.forms import Widget


class IconPickerWidget(TextInput):
    template_name = "icon_picker_widget.html"

    class Media:
        js = ("/static/vendor/universal-icon-picker/assets/js/universal-icon-picker.min.js",)

    def format_value(self, value):
        if value is None:
            return ""
        return value

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["id"] = name
        context["widget"]["value"] = self.format_value(value)
        context["widget"]["disabled"] = True
        return context


class SliderWidget(Widget):
    template_name = "slider_widget.html"
    input_type = "range"

    class Media:
        js = ("/static/js/slider_widget.js",)

    def __init__(self, attrs=None, smin=0, smax=0):
        self.smin = smin
        self.smax = smax
        super().__init__(attrs)


class SwitchWidget(Widget):
    template_name = "switch_widget.html"


class MarkdownWidget(Textarea):
    template_name = "markdown_widget.html"

    class Media:
        js = ("/static/js/markdown_widget.js", "/static/vendor/marked/marked.min.js")

    def __init__(self):
        attrs = {"class": "markdown-widget"}
        super().__init__(attrs)
