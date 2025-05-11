from __future__ import annotations

import logging

from django import template
from django.template import Context
from django.template import Template
from django.utils.safestring import mark_safe

logger = logging.getLogger("bornhack.%s" % __name__)
register = template.Library()


def render_datetime(datetime):
    """Renders a datetime in the users timezone"""
    t = Template("{{ datetime }}")
    return t.render(Context({"datetime": datetime}))


def render_datetimetzrange(datetimetzrange):
    """Renders a datetimetzrange as 14:00-16:00 in the users timezone"""
    return f"{render_datetime(datetimetzrange.lower.time())}-{render_datetime(datetimetzrange.upper.time())} ({datetimetzrange.lower.tzname()})"


@register.simple_tag
def availabilitytable(matrix, form=None):
    """Build the HTML table to show speaker availability, and hold the checkboxes
    for the speaker_availability form.
    """
    if not matrix:
        logger.error("we have no matrix to build a table from")
        return ""

    # start bulding the output
    output = "<div class='form-group'>"
    output += "<table class='table table-hover table-condensed table-bordered table-responsive' style='margin-bottom: .25em;'><thead>"
    output += "<tr><th class='text-nowrap'>Speaker Availability</th>"

    # to build the <thead> for this table we need to loop over the days (dates)
    # in the matrix and create a column for each
    for date in matrix.keys():
        output += f"<th>{render_datetime(date.lower.date())}</th>"
    output += "</tr></thead>"
    output += "<tbody>"

    # loop over all dates in the matrix to find a set of unique "daychunks" we
    # need checkboxes for. We need to represent a daychunk with a <tr> table row if
    # just one of the days need a checkbox for it.
    chunks = set()
    for date in matrix.keys():
        # loop over the daychunks on this date
        for daychunk in matrix[date].keys():
            if matrix[date][daychunk]:
                # add this daychunk it to the chunks set
                chunks.add(render_datetimetzrange(daychunk))
    # make chunks a list and sort it
    chunks = list(chunks)
    chunks.sort()

    needsinfo = False
    # loop over chunks where at least one date needs a checkbox
    for chunk in chunks:
        # we need a header row for this chunk
        output += f"<tr><th class='text-nowrap'>{chunk}</th>"
        # loop over dates to find out if we need a checkbox for this chunk on this date
        for date in matrix.keys():
            # loop over matrix daychunks and for each date find the chunk/row we are working with
            for daychunk in matrix[date].keys():
                if render_datetimetzrange(daychunk) == chunk:
                    # do we need a checkbox?
                    if matrix[date][daychunk]:
                        popup = f'<div class="text-left"><p>{render_datetime(daychunk.lower.date)} from {render_datetime(daychunk.lower.time)} to {render_datetime(daychunk.upper.time)}.</p>'

                        popup += "<p>This time slot is used for:<br>"
                        for et in matrix[date][daychunk]["event_types"]:
                            popup += f'<i class="fas fa-{et["icon"]} fa-fw" style="color: {et["color"]};"></i> {et["name"]}s<br>'
                        popup += "</p>"

                        # set tdclass and popup message depending on availability info in our db
                        if matrix[date][daychunk]["initial"]:
                            tdclass = "success"
                            tdicon = "check"
                            popup += "<p>Our records indicate that this person is <b>available</b> during this time slot.</p>"
                        elif matrix[date][daychunk]["initial"] is None:
                            tdclass = "warning"
                            tdicon = "question"
                            needsinfo = True
                            if form:
                                popup += "<p>We have no existing records about this persons availability during this time slot. Please submit availability information!</p>"
                            else:
                                popup += "<p>We have no existing records about this persons availability during this time slot.</p>"

                        else:
                            tdclass = "danger"
                            tdicon = "times"
                            popup += "<p>Our records indicate that this person is <b>not available</b> during this time slot.</p>"

                        # ok finish the popup and add it to the td
                        popup += "</div>"

                        # add the <td> with label and the field from the form
                        output += f"<td class='text-center {tdclass}' style='padding: 1px; vertical-align: middle;'>"
                        # add the form field?
                        if form:
                            # add the label for this form field, include an
                            # onclick() js event to the label to toggle the td background class
                            output += f"<label for='id_{matrix[date][daychunk]['fieldname']}' style='display: block; margin-bottom: 0px;' onclick='toggle_sa_form_class(\"id_{matrix[date][daychunk]['fieldname']}\");'>&nbsp;"
                            output += str(form[matrix[date][daychunk]["fieldname"]])
                        else:
                            output += f'<i class="fas fa-{tdicon}"></i>'

                        # add the info icon
                        output += f"<i class='fas fa-info-circle float-end text-info' data-bs-toggle='tooltip' data-bs-html='true' data-bs-placement='right' data-bs-title='{popup}' style='margin-left: -20px;margin-right: 10px;'>"
                        if form:
                            output += "</label>"
                        output += "</td>"
                    else:
                        output += "<td class='text-center active'>N/A</td>"
        output += "</tr>"

    # finish the table and add the help text
    output += "</table>"
    if form:
        output += "<div class='help-block'>Please uncheck any boxes where this person is not available</div>"
    elif needsinfo:
        output += '<div class="alert alert-warning" role="alert"><i class="fas fa-exclamation-triangle"></i> We have missing availability information for this person!</div>'

    output += "</div>"
    return mark_safe(output)
