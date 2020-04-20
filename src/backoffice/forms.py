from django import forms
from program.models import Speaker


class AutoScheduleValidateForm(forms.Form):
    schedule = forms.ChoiceField(
        choices=(
            (
                "current",
                "Validate Current Schedule (Load the AutoScheduler with the currently scheduled Events and validate)",
            ),
            (
                "similar",
                "Validate Similar Schedule (Create and validate a new schedule based on the current schedule)",
            ),
            ("new", "Validate New Schedule (Create and validate a new schedule)"),
        ),
        help_text="What to validate?",
    )


class AutoScheduleApplyForm(forms.Form):
    schedule = forms.ChoiceField(
        choices=(
            (
                "similar",
                "Apply Similar Schedule (Create and apply a new schedule similar to the current schedule)",
            ),
            (
                "new",
                "Apply New Schedule (Create and apply a new schedule without considering the current schedule)",
            ),
        ),
        help_text="Which schedule to apply?",
    )


class EventScheduleForm(forms.Form):
    """ The EventSlots are added in the view """

    pass


class SpeakerForm(forms.ModelForm):
    class Meta:
        model = Speaker
        fields = [
            "name",
            "email",
            "biography",
            "needs_oneday_ticket",
        ]

    def __init__(self, matrix={}, *args, **kwargs):
        """
        initialise the form and adapt based on event_type
        """
        super().__init__(*args, **kwargs)

        if matrix:
            # add speaker availability fields
            for date in matrix.keys():
                # do we need a column for this day?
                if matrix[date]:
                    # loop over the daychunks for this day
                    for daychunk in matrix[date]:
                        if matrix[date][daychunk]:
                            # add the field
                            self.fields[
                                matrix[date][daychunk]["fieldname"]
                            ] = forms.BooleanField(required=False)
                            # add it to Meta.fields too
                            self.Meta.fields.append(matrix[date][daychunk]["fieldname"])
        else:
            print("no matrix")
