import icalendar
from icalendar import vDatetime


def gen_icalevents(event):
    for i in event.days.all():
        ievent = icalendar.Event()
        ievent['summary'] = event.title

        newdate = datetime.datetime.combine(i.date, datetime.time(event.start.hour, event.start.minute, event.start.second))
        ievent['dtstart'] = vDatetime(newdate).to_ical()

        newdate = datetime.datetime.combine(i.date, datetime.time(event.end.hour, event.end.minute, event.end.second))
        ievent['dtend'] = vDatetime(newdate).to_ical()

        yield ievent

def gen_ics(events):
    cal = icalendar.Calendar()
    for event in events:
        for ical_event in gen_icalevents(event):
            cal.add_component(ical_event)
    return cal.to_ical()


