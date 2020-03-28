import numpy as np


def schedule_to_array(schedule, events, slots):
    """Convert a schedule from schedule to array form
    Parameters
    ----------
    schedule : list or tuple
        of instances of :py:class:`resources.ScheduledItem`
    events : list or tuple
        of :py:class:`resources.Event` instances
    slots : list or tuple
        of :py:class:`resources.Slot` instances
    Returns
    -------
    np.array
        An E by S array (X) where E is the number of events and S the
        number of slots. Xij is 1 if event i is scheduled in slot j and
        zero otherwise
    """
    array = np.zeros((len(events), len(slots)), dtype=np.int8)
    for item in schedule:
        array[events.index(item.event), slots.index(item.slot)] = 1
    return array


def number_of_changes(slots, events, original_schedule, X, **kwargs):
    """
    A function that counts the number of changes between a given schedule
    and an array (either numpy array of lp array).
    """
    changes = 0
    original_array = schedule_to_array(original_schedule, events=events, slots=slots)
    for row, event in enumerate(original_array):
        for col, slot in enumerate(event):
            if slot == 0:
                changes += X[row, col]
            else:
                changes += 1 - X[row, col]
    return changes
