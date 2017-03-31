import icalendar

def gen_ics(eventinstances):
    cal = icalendar.Calendar()
    for eventinstance in eventinstances:
        ievent = icalendar.Event()
        ievent['summary'] = eventinstance.event.title
        ievent['dtstart'] = icalendar.vDatetime(eventinstance.when.lower).to_ical()
        ievent['dtend'] = icalendar.vDatetime(eventinstance.when.upper).to_ical()
        cal.add_component(ievent)
    return cal.to_ical()


