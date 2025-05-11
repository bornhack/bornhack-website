"""Borrowed from https://gist.github.com/schinckel/aeea9c0f807dd009bf47566df7ac5054

This module overrides the Range.__and__ function, so that it returns a boolean value
based on if the two objects overlap.
The rationale behind this is that it mirrors the `range && range` operator in postgres.
There are tests for this, that hit the database with randomly generated ranges and ensure
that the database and this method agree upon the results.
There is also a more complete `isempty()` method, which examines the bounds types and values,
and determines if the object is indeed empty. This is required when python-created range objects
are dealt with, as these are not normalised the same way that postgres does.
"""

from __future__ import annotations

import datetime

from psycopg2.extras import Range

OFFSET = {
    int: 1,
    datetime.date: datetime.timedelta(1),
}


def normalise(instance):
    """In the case of discrete ranges (integer, date), then we normalise the values
    so it is in the form [start,finish), the same way that postgres does.
    If the lower value is None, we normalise this to (None,finish)
    """
    if instance.isempty:
        return instance

    lower = instance.lower
    upper = instance.upper
    bounds = list(instance._bounds)

    if lower is not None and lower == upper and instance._bounds != "[]":
        return instance.__class__(empty=True)

    if lower is None:
        bounds[0] = "("
    elif bounds[0] == "(" and type(lower) in OFFSET:
        lower += OFFSET[type(lower)]
        bounds[0] = "["

    if upper is None:
        bounds[1] = ")"
    elif bounds[1] == "]" and type(upper) in OFFSET:
        upper += OFFSET[type(upper)]
        bounds[1] = ")"

    if lower is not None and lower == upper and bounds != ["[", "]"]:
        return instance.__class__(empty=True)

    return instance.__class__(lower, upper, "".join(bounds))


def __and__(self, other):
    if not isinstance(other, self.__class__):
        raise TypeError(
            f"unsupported operand type(s) for &: '{self.__class__.__name__}' and '{other.__class__.__name__}'",
        )

    self = normalise(self)
    other = normalise(other)

    # If _either_ object is empty, then it will never overlap with any other one.
    if self.isempty or other.isempty:
        return False

    if other < self:
        return other & self

    # Because we can't compare None with a datetime.date(), we need to deal
    # with the cases where one (or both) of the parts are None first.
    if self.lower is None:
        if self.upper is None or other.lower is None:
            return True
        if self.upper_inc and other.lower_inc:
            return self.upper >= other.lower
        return self.upper > other.lower

    if self.upper is None:
        if other.upper is None:
            return True
        if self.lower_inc and other.upper_inc:
            return self.lower <= other.upper
        return self.lower < other.upper

    # Now, all we care about is self.upper_inc and other.lower_inc
    if self.upper_inc and other.lower_inc:
        return self.upper >= other.lower
    return self.upper > other.lower


def __eq__(self, other):
    if not isinstance(other, Range):
        return False

    self = normalise(self)
    other = normalise(other)

    return self._lower == other._lower and self._upper == other._upper and self._bounds == other._bounds


def range_merge(self, other):
    """Union"""
    self = normalise(self)
    other = normalise(other)
    bounds = [None, None]

    if self.isempty:
        return self

    if other.isempty:
        return other

    if self > other:
        self, other = other, self

    if self.upper is not None and other.lower is not None:
        if not self.upper_inc and other.lower <= self.upper:
            # They overlap.
            pass
        else:
            raise ValueError("Result of range union would not be contiguous")

    if self.lower is None:
        lower = None
        bounds[0] = "("
    elif self.lower_inc != other.lower_inc:
        # The bounds differ, so we need to use the complicated logic.
        raise NotImplementedError
    else:
        # The bounds are the same, so we can just use the lower value.
        lower = min(self.lower, other.lower)
        bounds[0] = self._bounds[0]

    if self.upper is None or other.upper is None:
        upper = None
        bounds[1] = ")"
    elif self.upper_inc != other.upper_inc:
        raise NotImplementedError
    else:
        upper = max(self.upper, other.upper)
        bounds[1] = self._bounds[1]

    return normalise(self.__class__(lower, upper, "".join(bounds)))


def range_intersection(self, other):
    self = normalise(self)
    other = normalise(other)

    if not self & other:
        return self.__class__(empty=True)

    # We need to use custom comparisons because non-number range types will fail to compare.
    # Also, min(X, None) means min(X, Infinity), really.
    if self.lower is None:
        lower = other.lower
    elif other.lower is None:
        lower = self.lower
    else:
        lower = max(self.lower, other.lower)

    if self.upper is None:
        upper = other.upper
    elif other.upper is None:
        upper = self.upper
    else:
        upper = min(self.upper, other.upper)

    return normalise(self.__class__(lower, upper, "[)"))


def range_contains(self, other):
    if self._bounds is None:
        return False

    if type(self) is type(other):
        return self & other and self + other == self

    # We have two tests to make in each case - is the value out of the lower bound,
    # and is the value out on the upper bound. We can make a series of tests, and if we ever find
    # a situation where we _are_ out of bounds, return at that point.

    if self.lower is not None:
        if self.lower_inc:
            if other < self.lower:
                return False
        elif other <= self.lower:
            return False

    if self.upper is not None:
        if self.upper_inc:
            if other > self.upper:
                return False
        elif other >= self.upper:
            return False

    return True


def deconstruct(self):
    return (
        f"{self.__class__.__module__}.{self.__class__.__name__}",
        [self.lower, self.upper, self._bounds],
        {},
    )


Range.__add__ = range_merge
Range.__and__ = __and__
Range.__eq__ = __eq__
Range.__mul__ = range_intersection
Range.__contains__ = range_contains

Range.deconstruct = deconstruct


_BOUNDS_SWAP = {
    "[": ")",
    "]": "(",
    "(": "]",
    ")": "[",
}.get


def safe_subtract(initial, subtract):
    """Subtract the range "subtract" from the range "initial".
    Always return an array of ranges (which may be empty).
    """
    _Range = initial.__class__
    sub_bounds = "".join(map(_BOUNDS_SWAP, subtract._bounds))

    # Simplest case - ranges are the same, or the source one is fully contained within
    # the subtracting one, then we get an empty list of ranges.
    if subtract == initial or initial in subtract:
        return []

    # If the ranges don't overlap, then we retain the source.
    if not initial & subtract:
        return [initial]

    # We will have either one or two objects, depending upon if the subtractor overlaps one of the bounds or not.
    # We know that both of them will not overlap the bounds, because that case has already been dealt with.

    if initial.upper in subtract or (not initial.upper_inc and initial.upper == subtract.upper):
        return [
            _Range(
                initial.lower,
                subtract.lower,
                f"{initial._bounds[0]}{sub_bounds[0]}",
            ),
        ]
    if initial.lower in subtract or (not initial.lower_inc and initial.lower == subtract.lower):
        return [
            _Range(
                subtract.upper,
                initial.upper,
                f"{sub_bounds[1]}{initial._bounds[1]}",
            ),
        ]
    return [
        _Range(
            initial.lower,
            subtract.lower,
            f"{initial._bounds[0]}{sub_bounds[0]}",
        ),
        _Range(
            subtract.upper,
            initial.upper,
            f"{sub_bounds[1]}{initial._bounds[1]}",
        ),
    ]


def array_subtract(initial, subtract):
    """Subtract the range from each item in the initial array."""
    result = []
    for _range in initial:
        result.extend(safe_subtract(_range, subtract))
    return result


def array_subtract_all(initial, subtract):
    """Subtract all overlapping ranges in subtract from all ranges in initial."""
    result = list(initial)
    for other in subtract:
        result = array_subtract(result, other)
    return result
