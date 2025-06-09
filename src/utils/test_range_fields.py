from __future__ import annotations

import datetime
from decimal import Decimal

from django.db import connection
from hypothesis import given
from hypothesis.extra.django import TestCase
from hypothesis.strategies import dates
from hypothesis.strategies import datetimes
from hypothesis.strategies import integers
from hypothesis.strategies import none
from hypothesis.strategies import one_of
from hypothesis.strategies import sampled_from
from hypothesis.strategies import tuples
from psycopg2.extras import DateRange
from psycopg2.extras import DateTimeRange
from psycopg2.extras import NumericRange
from psycopg2.extras import Range

from .range_fields import array_subtract_all
from .range_fields import normalise
from .range_fields import safe_subtract


def valid_range(obj):
    return obj[0] is None or obj[1] is None or obj[0] <= obj[1]


BOUNDS = sampled_from(["[]", "()", "[)", "(]"])
BIGINT = one_of(
    integers(min_value=-9223372036854775807, max_value=+9223372036854775806),
    none(),
)
DATES = one_of(dates(), none())
DATETIMES = one_of(datetimes(), none())

num_range = tuples(BIGINT, BIGINT, BOUNDS).filter(valid_range)
date_range = tuples(DATES, DATES, BOUNDS).filter(valid_range)
datetime_range = tuples(DATETIMES, DATETIMES, BOUNDS).filter(valid_range)


class TestRange__and__(TestCase):
    def test_normalised(self):
        self.assertTrue(normalise(NumericRange(0, 1, "()")).isempty)
        self.assertFalse(
            normalise(
                DateRange(datetime.date(2000, 1, 9), datetime.date(2000, 1, 10), "(]"),
            ).isempty,
        )
        self.assertTrue(normalise(NumericRange(2, 2, "()")).isempty)

    @given(num_range)
    def test_normalise_hypothesis(self, a):
        a = NumericRange(*a)
        cursor = connection.cursor()
        cursor.execute("SELECT %s::int8range", [a])
        self.assertEqual(cursor.fetchone()[0], normalise(a), a)

    @given(date_range)
    def test_normalise_hypothesis_daterange(self, a):
        a = DateRange(*a)
        cursor = connection.cursor()
        cursor.execute("SELECT %s::daterange", [a])
        self.assertEqual(cursor.fetchone()[0], normalise(a), a)

    @given(datetime_range)
    def test_normalise_hypothesis_tsrange(self, a):
        a = DateTimeRange(*a)
        cursor = connection.cursor()
        cursor.execute("SELECT %s::tsrange", [a])
        self.assertEqual(cursor.fetchone()[0], normalise(a), a)

    def test_can_query_db(self):
        cursor = connection.cursor()
        cursor.execute(
            "SELECT %s::int8range && %s::int8range",
            [NumericRange(), NumericRange()],
        )
        self.assertTrue(cursor.fetchone()[0])

    def test_may_not_compare_different_range_types(self):
        with self.assertRaises(TypeError):
            NumericRange() & DateRange()

    def test_empty_ranges_do_not_overlap(self):
        self.assertFalse(NumericRange(0, 0, "()") & NumericRange())
        self.assertFalse(NumericRange(0, 1, "()") & NumericRange(None, None, "[]"))

    def test_two_full_ranges_overlap(self):
        self.assertTrue(NumericRange() & NumericRange())
        self.assertTrue(NumericRange(None, None, "[]") & NumericRange(None, None, "[]"))

    def test_full_range_overlaps_non_full_range(self):
        self.assertTrue(NumericRange() & NumericRange(-12, 55))
        self.assertTrue(NumericRange(-12, 55) & NumericRange())

    def test_ends_touch(self):
        self.assertFalse(NumericRange(10, 20) & NumericRange(20, 30))
        self.assertTrue(NumericRange(10, 20, "[]") & NumericRange(20, 30))
        self.assertFalse(NumericRange(20, 30) & NumericRange(10, 20))
        self.assertTrue(NumericRange(20, 30) & NumericRange(10, 20, "[]"))

        self.assertFalse(NumericRange(10, 20) & NumericRange(20, None))
        self.assertTrue(NumericRange(10, 20, "[]") & NumericRange(20, None))
        self.assertFalse(NumericRange(20, None) & NumericRange(10, 20))
        self.assertTrue(NumericRange(20, None) & NumericRange(10, 20, "[]"))

        self.assertFalse(NumericRange(None, 20) & NumericRange(20, 30))
        self.assertTrue(NumericRange(None, 20, "[]") & NumericRange(20, 30))
        self.assertFalse(NumericRange(20, 30) & NumericRange(None, 20))
        self.assertTrue(NumericRange(20, 30) & NumericRange(None, 20, "[]"))

        self.assertFalse(NumericRange(None, 20) & NumericRange(20, None))
        self.assertTrue(NumericRange(None, 20, "[]") & NumericRange(20, None))
        self.assertFalse(NumericRange(20, None) & NumericRange(None, 20))
        self.assertTrue(NumericRange(20, None) & NumericRange(None, 20, "[]"))

        self.assertFalse(NumericRange(0, 2, "()") & NumericRange(0, 0, "[]"))

    def test_both_upper_None(self):
        self.assertTrue(NumericRange(1, None), NumericRange(100, None))

    @given(num_range, num_range)
    def test_with_hypothesis(self, a, b):
        a = NumericRange(*a)
        b = NumericRange(*b)
        cursor = connection.cursor()
        cursor.execute("SELECT %s::int8range && %s::int8range", [a, b])
        self.assertEqual(cursor.fetchone()[0], a & b, f"{a} && {b}")

    @given(date_range, date_range)
    def test_with_hypothesis_dates(self, a, b):
        a = DateRange(*a)
        b = DateRange(*b)
        cursor = connection.cursor()
        cursor.execute("SELECT %s::daterange && %s::daterange", [a, b])
        self.assertEqual(cursor.fetchone()[0], a & b, f"{a} && {b}")

    @given(datetime_range, datetime_range)
    def test_with_hypothesis_datetimes(self, a, b):
        a = DateTimeRange(*a)
        b = DateTimeRange(*b)
        cursor = connection.cursor()
        cursor.execute("SELECT %s::tsrange && %s::tsrange", [a, b])
        self.assertEqual(cursor.fetchone()[0], a & b, f"{a} && {b}")

    def test_with_values_found_by_hypothesis(self):
        self.assertEqual(
            NumericRange(None, 1, "()"),
            normalise(NumericRange(None, 0, "[]")),
        )
        self.assertFalse(NumericRange(0, None, "()") & NumericRange(None, 1, "()"))

    @given(datetime_range)
    def test_equality(self, a):
        self.assertNotEqual(a, None)
        self.assertNotEqual(a, 1)
        self.assertNotEqual(a, [])
        self.assertEqual(a, a)

    def test_manual_equality(self):
        self.assertFalse(NumericRange(0, 2, "[]") is None)

    def test_timedelta_ranges(self):
        a = Range(datetime.timedelta(0), datetime.timedelta(1))
        b = Range(datetime.timedelta(hours=5), datetime.timedelta(hours=9))

        self.assertTrue(a & b)
        self.assertTrue(b & a)
        self.assertTrue(b.lower in a)
        self.assertTrue(b.upper in a)
        self.assertFalse(a.lower in b)
        self.assertFalse(a.upper in b)


class TestRangeContains(TestCase):
    def test_out_of_bounds(self):
        self.assertFalse(2 in Range(7, 12))
        self.assertFalse(6 in Range(1, 4))
        self.assertFalse(2 in Range(6, None))
        self.assertFalse(22 in Range(None, 20))

        self.assertFalse(Decimal("8.01") in Range(0, 8, "[]"))
        self.assertFalse(Decimal(8) in Range(0, 8, "[)"))

    def test_in_bounds(self):
        self.assertTrue(4 in Range(0, 8))
        self.assertTrue(4 in Range(None, 8))
        self.assertTrue(4 in Range(0, None))
        self.assertTrue(4 in Range(None, None))

    def test_in_on_lower_bounds_inclusive(self):
        self.assertTrue(2 in Range(2, 7))
        self.assertTrue(2 in Range(2, None))

    def test_out_on_lower_bounds_exclusive(self):
        self.assertFalse(2 in Range(2, 7, "()"))
        self.assertFalse(2 in Range(2, None, "()"))
        self.assertFalse(2 in Range(2, 7, "(]"))

    def test_in_on_upper_bounds_inclusive(self):
        self.assertTrue(10 in Range(0, 10, "[]"))
        self.assertTrue(10 in Range(0, 10, "(]"))
        self.assertTrue(10 in Range(None, 10, "(]"))

    def test_out_on_upper_bounds_exclusive(self):
        self.assertFalse(10 in Range(0, 10, "[)"))
        self.assertFalse(10 in Range(None, 10, "()"))
        self.assertFalse(10 in Range(0, 10, "()"))

    def test_no_overlap(self):
        self.assertFalse(Range(2, 4) in Range(8, 12))

    def test_partial_overlap(self):
        self.assertFalse(Range(2, 10) in Range(8, 12))

    def test_in_is_larger(self):
        self.assertFalse(Range(2, 14) in Range(8, 12))

    def test_match(self):
        self.assertTrue(Range(2, 4) in Range(2, 4))
        self.assertTrue(Range(2, 4, "[)") in Range(2, 4, "[]"))
        self.assertFalse(Range(2, 4, "[]") in Range(2, 4, "[)"))


class TestRangeMerge(TestCase):
    def test_contained(self):
        self.assertEqual(Range(1, 12) + Range(2, 5), Range(1, 12))
        self.assertEqual(Range(2, 5) + Range(1, 12), Range(1, 12))
        self.assertEqual(Range(None, None) + Range(2, 44), Range(None, None))
        self.assertEqual(Range(2, 44) + Range(None, None), Range(None, None))
        self.assertEqual(Range(None, 44) + Range(None, None), Range(None, None))

    def test_intersect(self):
        self.assertEqual(Range(None, 5) + Range(2, None), Range(None, None))

    def test_adjacent(self):
        self.assertEqual(Range(2, 22, "[]") + Range(23, 44), Range(2, 44))

    def test_distinct(self):
        with self.assertRaises(ValueError):
            Range(2, 6) + Range(8, 12)


class TestRangeIntersect(TestCase):
    def test_intersects(self):
        self.assertEqual(Range(22, 25, "[]") * Range(23, 28, "[]"), Range(23, 25, "[]"))
        self.assertEqual(
            Range(None, 25, "(]") * Range(23, None, "[)"),
            Range(23, 25, "[]"),
        )


class TestRangeSubtract(TestCase):
    def test_source_within_subtract(self):
        """[ source )
        [    subtract    )
        [    subtract    ]
        (    subtract    )
        (    subtract    ]
        """
        self.assertEqual([], safe_subtract(Range(11, 16, "[)"), Range(0, 44, "[)")))
        self.assertEqual([], safe_subtract(Range(11, 16, "[)"), Range(0, 44, "(]")))
        self.assertEqual([], safe_subtract(Range(11, 16, "[)"), Range(0, 44, "()")))
        self.assertEqual([], safe_subtract(Range(11, 16, "[)"), Range(0, 44, "[]")))

        """
            (source)
        [   subtract   ]
           ... etc
        """

        self.assertEqual([], safe_subtract(Range(11, 16, "()"), Range(0, 44, "[)")))
        self.assertEqual([], safe_subtract(Range(11, 16, "()"), Range(0, 44, "(]")))
        self.assertEqual([], safe_subtract(Range(11, 16, "()"), Range(0, 44, "()")))
        self.assertEqual([], safe_subtract(Range(11, 16, "()"), Range(0, 44, "[]")))

        self.assertEqual([], safe_subtract(Range(11, 16, "[]"), Range(0, 44, "[)")))
        self.assertEqual([], safe_subtract(Range(11, 16, "[]"), Range(0, 44, "(]")))
        self.assertEqual([], safe_subtract(Range(11, 16, "[]"), Range(0, 44, "()")))
        self.assertEqual([], safe_subtract(Range(11, 16, "[]"), Range(0, 44, "[]")))

        self.assertEqual([], safe_subtract(Range(11, 16, "(]"), Range(0, 44, "[)")))
        self.assertEqual([], safe_subtract(Range(11, 16, "(]"), Range(0, 44, "(]")))
        self.assertEqual([], safe_subtract(Range(11, 16, "(]"), Range(0, 44, "()")))
        self.assertEqual([], safe_subtract(Range(11, 16, "(]"), Range(0, 44, "[]")))

    def test_subtract_upper_bound_matches_source_lower_bound(self):
        """[ source )
        [subtract]

        """
        self.assertEqual(
            [Range(4, 7, "()")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 4, "[]")),
        )

    def test_subtract_lower_bound_below_bounds_only(self):
        """[source)
        [subtract)
        (subtract)

        """
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 4, "[)")),
        )
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 4, "()")),
        )

        """
                 (source)
        (subtract]
        """
        self.assertEqual(
            [Range(4, 7, "()")],
            safe_subtract(Range(4, 7, "()"), Range(0, 4, "[]")),
        )

    def test_subtract_lower_bound_below_completely(self):
        """[source)
        [subtract]
        [subtract)
        [subtract]
        (subtract)

        """
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 3, "[)")),
        )
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 3, "()")),
        )
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 3, "[]")),
        )
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 3, "(]")),
        )

        # Other source bounds types
        self.assertEqual(
            [Range(4, 7, "[]")],
            safe_subtract(Range(4, 7, "[]"), Range(0, 3, "[)")),
        )
        self.assertEqual(
            [Range(4, 7, "[]")],
            safe_subtract(Range(4, 7, "[]"), Range(0, 3, "()")),
        )
        self.assertEqual(
            [Range(4, 7, "[]")],
            safe_subtract(Range(4, 7, "[]"), Range(0, 3, "[]")),
        )
        self.assertEqual(
            [Range(4, 7, "[]")],
            safe_subtract(Range(4, 7, "[]"), Range(0, 3, "(]")),
        )

        self.assertEqual(
            [Range(4, 7, "(]")],
            safe_subtract(Range(4, 7, "(]"), Range(0, 3, "[)")),
        )
        self.assertEqual(
            [Range(4, 7, "(]")],
            safe_subtract(Range(4, 7, "(]"), Range(0, 3, "()")),
        )
        self.assertEqual(
            [Range(4, 7, "(]")],
            safe_subtract(Range(4, 7, "(]"), Range(0, 3, "[]")),
        )
        self.assertEqual(
            [Range(4, 7, "(]")],
            safe_subtract(Range(4, 7, "(]"), Range(0, 3, "(]")),
        )

        self.assertEqual(
            [Range(4, 7, "()")],
            safe_subtract(Range(4, 7, "()"), Range(0, 3, "[)")),
        )
        self.assertEqual(
            [Range(4, 7, "()")],
            safe_subtract(Range(4, 7, "()"), Range(0, 3, "()")),
        )
        self.assertEqual(
            [Range(4, 7, "()")],
            safe_subtract(Range(4, 7, "()"), Range(0, 3, "[]")),
        )
        self.assertEqual(
            [Range(4, 7, "()")],
            safe_subtract(Range(4, 7, "()"), Range(0, 3, "(]")),
        )

    def test_upper_bound_above_bounds_only(self):
        """[source)
               [subtract]

        [source]
               (subtract)
        """
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(7, 10, "[)")),
        )
        self.assertEqual(
            [Range(4, 7, "[]")],
            safe_subtract(Range(4, 7, "[]"), Range(7, 10, "()")),
        )

        """
        [source]
               [subtract]
        """
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[]"), Range(7, 12, "[]")),
        )

    def test_upper_bound_above_completely(self):
        """[source)
        [subtract]
        (subtract)
        [subtract)
        (subtract]

        """
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(10, 14, "[]")),
        )
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(10, 14, "()")),
        )
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(10, 14, "[)")),
        )
        self.assertEqual(
            [Range(4, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(10, 14, "(]")),
        )

    def test_intersects_lower_bounds(self):
        """[source)
        [subtract]
             [subtract]
             [subtract)
             (subtract)

        """
        self.assertEqual(
            [Range(4, 7, "()")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 4, "[]")),
        )
        self.assertEqual(
            [Range(5, 7, "()")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 5, "[]")),
        )
        self.assertEqual(
            [Range(5, 7, "[)")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 5, "[)")),
        )
        self.assertEqual(
            [Range(5, 7, "()")],
            safe_subtract(Range(4, 7, "[)"), Range(0, 5, "[]")),
        )

    def test_lower_bounds_same(self):
        """[source        )

        [subtract]
        [subtract)
        (subtract)
        (subtract]
        (   subtract   )
        (   subtract   ]
        """
        self.assertEqual(
            [Range(6, 8, "()")],
            safe_subtract(Range(4, 8), Range(4, 6, "[]")),
        )
        self.assertEqual(
            [Range(6, 8, "[)")],
            safe_subtract(Range(4, 8), Range(4, 6, "[)")),
        )

        self.assertEqual(
            [Range(4, 4, "[]"), Range(6, 8, "[)")],
            safe_subtract(Range(4, 8), Range(4, 6, "()")),
        )
        self.assertEqual(
            [Range(4, 4, "[]"), Range(6, 8, "()")],
            safe_subtract(Range(4, 8), Range(4, 6, "(]")),
        )

    def test_lower_bound_inclusive_difference_only(self):
        """[source   )
        (subtract )
        (subtract ]
        """
        self.assertEqual(
            [Range(4, 4, "[]")],
            safe_subtract(Range(4, 8, "[)"), Range(4, 8, "(]")),
        )
        self.assertEqual(
            [Range(4, 4, "[]")],
            safe_subtract(Range(4, 8, "[)"), Range(4, 8, "()")),
        )

    def test_intersects_upper_bound(self):
        """[source)

        [subtract]
        (subtract)
        """
        self.assertEqual(
            [Range(4, 6, "[)")],
            safe_subtract(Range(4, 8), Range(6, 12, "[]")),
        )
        self.assertEqual(
            [Range(4, 6, "[]")],
            safe_subtract(Range(4, 8), Range(6, 12, "()")),
        )

    def test_exact_match(self):
        """[  source  )
        [ subtract )


        (  source  )
        ( subtract )

        [  source  ]
        [ subtract ]

        (  source  ]
        ( subtract ]

        """
        self.assertEqual([], safe_subtract(Range(4, 8, "[)"), Range(4, 8, "[)")))
        self.assertEqual([], safe_subtract(Range(4, 8, "[]"), Range(4, 8, "[]")))
        self.assertEqual([], safe_subtract(Range(4, 8, "()"), Range(4, 8, "()")))
        self.assertEqual([], safe_subtract(Range(4, 8, "(]"), Range(4, 8, "(]")))

    def test_upper_bounds_match(self):
        """[  source  )
        [subtract)
        (subtract)
        """
        self.assertEqual(
            [Range(4, 5, "[)")],
            safe_subtract(Range(4, 8, "[)"), Range(5, 8, "[)")),
        )
        self.assertEqual(
            [Range(4, 5, "[]")],
            safe_subtract(Range(4, 8, "[)"), Range(5, 8, "()")),
        )

        """
        [  source  )
          [subtract]
          (subtract]
        """

        self.assertEqual(
            [Range(4, 5, "[)")],
            safe_subtract(Range(4, 8, "[)"), Range(5, 8, "[]")),
        )
        self.assertEqual(
            [Range(4, 5, "[]")],
            safe_subtract(Range(4, 8, "[)"), Range(5, 8, "(]")),
        )

    def test_subtract_within(self):
        """[    source    )
        [subtract]
        (subtract)
        [subtract)
        (subtract]
        """
        self.assertEqual(
            [Range(4, 5, "[)"), Range(7, 8, "()")],
            safe_subtract(Range(4, 8, "[)"), Range(5, 7, "[]")),
        )
        self.assertEqual(
            [Range(4, 5, "[]"), Range(7, 8, "[)")],
            safe_subtract(Range(4, 8, "[)"), Range(5, 7, "()")),
        )
        self.assertEqual(
            [Range(4, 5, "[)"), Range(7, 8, "[)")],
            safe_subtract(Range(4, 8, "[)"), Range(5, 7, "[)")),
        )
        self.assertEqual(
            [Range(4, 5, "[]"), Range(7, 8, "()")],
            safe_subtract(Range(4, 8, "[)"), Range(5, 7, "(]")),
        )

    def test_bounds_only_differ(self):
        """[ source ]
        (subtract)
        [subtract)
        (subtract]
        """
        self.assertEqual(
            [Range(4, 4, "[]"), Range(8, 8, "[]")],
            safe_subtract(Range(4, 8, "[]"), Range(4, 8, "()")),
        )
        self.assertEqual(
            [Range(8, 8, "[]")],
            safe_subtract(Range(4, 8, "[]"), Range(4, 8, "[)")),
        )
        self.assertEqual(
            [Range(4, 4, "[]")],
            safe_subtract(Range(4, 8, "[]"), Range(4, 8, "(]")),
        )

        """
        ( source )
        [subtract]
        [subtract)
        (subtract]
        """
        self.assertEqual([], safe_subtract(Range(4, 8, "()"), Range(4, 8, "[]")))
        self.assertEqual([], safe_subtract(Range(4, 8, "()"), Range(4, 8, "(]")))
        self.assertEqual([], safe_subtract(Range(4, 8, "()"), Range(4, 8, "[)")))

    def test_subtract_ranges(self):
        self.assertEqual(
            [Range(2, 6), Range(8, 12)],
            array_subtract_all(
                [Range(0, 6), Range(7, 18)],
                [Range(0, 2), Range(6, 8), Range(12, None)],
            ),
        )
