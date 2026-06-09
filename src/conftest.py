import pytest
from collections import namedtuple
from zoneinfo import ZoneInfo
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from camps.models import Camp
from utils.bootstrap.base import Bootstrap

tz = ZoneInfo(settings.TIME_ZONE)
BOOTSTRAP = Bootstrap()

## Camp fixtures

@pytest.fixture
def full_camp_details() -> dict:
    """Fixture for full camp list with all details."""
    return {
        2016: {
            'tagline': 'Initial Commit',
            'colour': '#004dff',
            'read_only': True,
            'buildup': (
                datetime(2016, 8, 25, 12, 0),
                datetime(2016, 8, 27, 12, 0),
            ),
            'camp': (
                datetime(2016, 8, 27, 12, 0),
                datetime(2016, 9, 3, 12, 0),
            ),
            'teardown': (
                datetime(2016, 9, 3, 12, 0),
                datetime(2016, 9, 5, 12, 0),
            ),
        },
        2017: {
            'tagline': 'Make Tradition',
            'colour': '#750787',
            'read_only': True,
            'buildup': (
                datetime(2017, 8, 20, 16, 0),
                datetime(2017, 8, 22, 12, 0),
            ),
            'camp': (
                datetime(2017, 8, 22, 12, 0),
                datetime(2017, 8, 29, 12, 0),
            ),
            'teardown': (
                datetime(2017, 8, 29, 12, 0),
                datetime(2017, 8, 31, 12, 0),
            ),
        },
        2018: {
            'tagline': 'scale it',
            'colour': '#008026',
            'read_only': True,
            'buildup': (
                datetime(2018, 8, 12, 16, 0),
                datetime(2018, 8, 16, 12, 0),
            ),
            'camp': (
                datetime(2018, 8, 16, 12, 0),
                datetime(2018, 8, 23, 12, 0),
            ),
            'teardown': (
                datetime(2018, 8, 23, 12, 0),
                datetime(2018, 8, 26, 16, 0),
            ),
        },
        2019: {
            'tagline': 'a new /home',
            'colour': '#ffed00',
            'read_only': True,
            'light_text': False,
            'kickoff': (
                datetime(2019, 3, 8, 8, 0),
                datetime(2019, 3, 10, 8, 0),
            ),
            'buildup': (
                datetime(2019, 8, 5, 8, 0),
                datetime(2019, 8, 8, 12, 0),
            ),
            'camp': (
                datetime(2019, 8, 8, 12, 0),
                datetime(2019, 8, 15, 12, 0),
            ),
            'teardown': (
                datetime(2019, 8, 15, 12, 0),
                datetime(2019, 8, 18, 12, 0),
            ),
        },
        2020: {
            'tagline': 'Make Clean',
            'colour': '#ff8c00',
            'read_only': True,
            'kickoff': (
                datetime(2020, 3, 28, 12, 0),
                datetime(2020, 3, 28, 19, 30),
            ),
            'buildup': (
                datetime(2020, 8, 7, 12, 0),
                datetime(2020, 8, 11, 12, 0),
            ),
            'camp': (
                datetime(2020, 8, 11, 12, 0),
                datetime(2020, 8, 18, 12, 0),
            ),
            'teardown': (
                datetime(2020, 8, 18, 12, 0),
                datetime(2020, 8, 21, 12, 0),
            ),
        },
        2021: {
            'tagline': 'Continuous Delivery',
            'colour': '#e40303',
            'read_only': True,
            'kickoff': (
                datetime(2021, 7, 19, 12, 0),
                datetime(2021, 7, 19, 19, 0),
            ),
            'buildup': (
                datetime(2021, 8, 15, 12, 0),
                datetime(2021, 8, 19, 12, 0),
            ),
            'camp': (
                datetime(2021, 8, 19, 12, 0),
                datetime(2021, 8, 26, 12, 0),
            ),
            'teardown': (
                datetime(2021, 8, 26, 12, 0),
                datetime(2021, 8, 29, 12, 0),
            ),
        },
        2022: {
            'tagline': 'black ~/hack',
            'colour': '#000000',
            'read_only': True,
            'kickoff': (
                datetime(2022, 5, 25, 12, 0),
                datetime(2022, 5, 29, 12, 0),
            ),
            'buildup': (
                datetime(2022, 7, 30, 12, 0),
                datetime(2022, 8, 3, 12, 0),
            ),
            'camp': (
                datetime(2022, 8, 3, 12, 0),
                datetime(2022, 8, 10, 12, 0),
            ),
            'teardown': (
                datetime(2022, 8, 10, 12, 0),
                datetime(2022, 8, 13, 12, 0),
            ),
        },
        2023: {
            'tagline': 'make legacy',
            'colour': '#613915',
            'read_only': True,
            'kickoff': (
                datetime(2023, 5, 17, 12, 0),
                datetime(2023, 5, 21, 12, 0),
            ),
            'buildup': (
                datetime(2023, 7, 29, 12, 0),
                datetime(2023, 8, 2, 12, 0),
            ),
            'camp': (
                datetime(2023, 8, 2, 12, 0),
                datetime(2023, 8, 9, 12, 0),
            ),
            'teardown': (
                datetime(2023, 8, 9, 12, 0),
                datetime(2023, 8, 12, 12, 0),
            ),
        },
        2024: {
            'tagline': 'Feature Creep',
            'colour': '#73d7ee',
            'read_only': False,
            'light_text': False,
            'kickoff': (
                datetime(2024, 5, 8, 12, 0),
                datetime(2024, 5, 12, 12, 0),
            ),
            'buildup': (
                datetime(2024, 7, 12, 12, 0),
                datetime(2024, 7, 17, 12, 0),
            ),
            'camp': (
                datetime(2024, 7, 17, 12, 0),
                datetime(2024, 7, 24, 12, 0),
            ),
            'teardown': (
                datetime(2024, 7, 24, 12, 0),
                datetime(2024, 7, 28, 12, 0),
            ),
        },
        2025: {
            'tagline': '10 Badges',
            'colour': '#ffafc7',
            'read_only': False,
            'light_text': False,
            'kickoff': (
                datetime(2025, 5, 26, 12, 0),
                datetime(2025, 6, 1, 12, 0),
            ),
            'buildup': (
                datetime(2025, 7, 10, 12, 0),
                datetime(2025, 7, 16, 12, 0),
            ),
            'camp': (
                datetime(2025, 7, 16, 12, 0),
                datetime(2025, 7, 23, 12, 0),
            ),
            'teardown': (
                datetime(2025, 7, 23, 12, 0),
                datetime(2025, 7, 26, 12, 0),
            ),
        },
        2026: {
            'tagline': 'Undecided',
            'colour': '#ffffff',
            'read_only': False,
            'light_text': False,
            'kickoff': (
                datetime(2026, 5, 11, 12, 0),
                datetime(2026, 5, 17, 12, 0),
            ),
            'buildup': (
                datetime(2026, 7, 11, 17, 0),
                datetime(2026, 7, 15, 12, 0),
            ),
            'camp': (
                datetime(2026, 7, 15, 12, 0),
                datetime(2026, 7, 22, 12, 0),
            ),
            'teardown': (
                datetime(2026, 7, 22, 12, 0),
                datetime(2026, 7, 27, 12, 0),
            ),
        },
        2027: {
            'tagline': 'Undecided',
            'colour': '#004dff',
            'read_only': True,
            'kickoff': (
                datetime(2027, 5, 3, 12, 0),
                datetime(2027, 5, 9, 12, 0),
            ),
            'buildup': (
                datetime(2027, 7, 15, 12, 0),
                datetime(2027, 7, 21, 12, 0),
            ),
            'camp': (
                datetime(2027, 7, 21, 12, 0),
                datetime(2027, 7, 28, 12, 0),
            ),
            'teardown': (
                datetime(2027, 7, 28, 12, 0),
                datetime(2027, 8, 1, 12, 0),
            ),
        },
        2028: {
            'tagline': 'Undecided',
            'colour': '#750787',
            'read_only': True,
            'kickoff': (
                datetime(2028, 5, 22, 12, 0),
                datetime(2028, 5, 28, 12, 0),
            ),
            'buildup': (
                datetime(2028, 7, 13, 12, 0),
                datetime(2028, 7, 19, 12, 0),
            ),
            'camp': (
                datetime(2028, 7, 19, 12, 0),
                datetime(2028, 7, 26, 12, 0),
            ),
            'teardown': (
                datetime(2028, 7, 26, 12, 0),
                datetime(2028, 7, 30, 12, 0),
            ),
        },
        2029: {
            'tagline': 'Undecided',
            'colour': '#008026',
            'read_only': True,
            'kickoff': (
                datetime(2029, 5, 7, 12, 0),
                datetime(2029, 5, 13, 12, 0),
            ),
            'buildup': (
                datetime(2029, 7, 12, 12, 0),
                datetime(2029, 7, 18, 12, 0),
            ),
            'camp': (
                datetime(2029, 7, 18, 12, 0),
                datetime(2029, 7, 25, 12, 0),
            ),
            'teardown': (
                datetime(2029, 7, 25, 12, 0),
                datetime(2029, 7, 29, 12, 0),
            ),
        },
        2030: {
            'tagline': 'Undecided',
            'colour': '#ffed00',
            'read_only': True,
            'light_text': False,
            'kickoff': (
                datetime(2030, 5, 27, 12, 0),
                datetime(2030, 6, 2, 12, 0),
            ),
            'buildup': (
                datetime(2030, 7, 11, 12, 0),
                datetime(2030, 7, 17, 12, 0),
            ),
            'camp': (
                datetime(2030, 7, 17, 12, 0),
                datetime(2030, 7, 24, 12, 0),
            ),
            'teardown': (
                datetime(2030, 7, 24, 12, 0),
                datetime(2030, 7, 28, 12, 0),
            ),
        },
        2031: {
            'tagline': 'Undecided',
            'colour': '#ff8c00',
            'read_only': True,
            'kickoff': (
                datetime(2031, 5, 19, 12, 0),
                datetime(2031, 5, 25, 12, 0),
            ),
            'buildup': (
                datetime(2031, 7, 10, 12, 0),
                datetime(2031, 7, 16, 12, 0),
            ),
            'camp': (
                datetime(2031, 7, 16, 12, 0),
                datetime(2031, 7, 23, 12, 0),
            ),
            'teardown': (
                datetime(2031, 7, 23, 12, 0),
                datetime(2031, 7, 27, 12, 0),
            ),
        },
    }


@pytest.fixture
def camp_factory(db, full_camp_details):
    """Fixture returning a camp factory function."""

    def create_camp(persist=False, **kwargs) -> Camp:
        """Create a Camp instance. Saves to DB if persist=True."""
        year = kwargs.pop("year") or timezone.now().year
        camp = full_camp_details[year]
        defaults = {
            "title": f"BornHack {year}",
            "tagline": camp["tagline"],
            "slug": f"bornhack-{year}",
            "shortslug": f"bornhack-{year}",
            "colour": camp["colour"],
            "light_text": camp.get("light_text", True),
            "kickoff": camp.get("kickoff"),
            "buildup": camp["buildup"],
            "camp": camp["camp"],
            "teardown": camp["teardown"],
        }

        defaults.update(kwargs)

        camp = Camp(**defaults)

        if persist:
            camp.save()

        return camp

    return create_camp


@pytest.fixture
def test_camps(camp_factory):
    """Fixture for previous, current and next year's camps."""
    year = timezone.now().year
    TestCamps = namedtuple('TestCamps', ['last', 'current', 'next'])
    return TestCamps(
        last=camp_factory(persist=True, year=year - 1),
        current=camp_factory(persist=True, year=year),
        next=camp_factory(persist=True, year=year + 1),
    )


@pytest.fixture
def camp(test_camps) -> Camp:
    """Fixture for current years camp."""
    return test_camps.current


## User fixtures

@pytest.fixture
def users(db) -> dict:
    """Fixture returning dict of users."""
    BOOTSTRAP.create_users(15)
    return BOOTSTRAP.users


@pytest.fixture
def admin(users) -> User:
    """Fixture returning an admin user."""
    return users["admin"]


## Pytest client fixtures

@pytest.fixture
def url():
    """Overwrite this url fixture inside the test class for views."""


@pytest.fixture
def user_client(client, users, url):
    """Fixture for user authenticated client with url."""
    client.force_login(users[0])
    client.url = url
    return client


@pytest.fixture
def admin_client(client, admin, url):
    """Fixture for admin authenticated client with url."""
    client.force_login(admin)
    client.url = url
    return client

