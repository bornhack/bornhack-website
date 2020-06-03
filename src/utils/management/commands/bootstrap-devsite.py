# coding: utf-8
import logging
import random
import sys
from datetime import datetime, timedelta

import factory
import pytz
from allauth.account.models import EmailAddress
from camps.models import Camp
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.crypto import get_random_string
from events.models import Routing, Type
from facilities.models import (
    Facility,
    FacilityFeedback,
    FacilityQuickFeedback,
    FacilityType,
)
from faker import Faker
from feedback.models import Feedback
from info.models import InfoCategory, InfoItem
from news.models import NewsItem
from profiles.models import Profile
from program.autoscheduler import AutoScheduler
from program.models import (
    Event,
    EventLocation,
    EventProposal,
    EventSession,
    EventSlot,
    EventTrack,
    EventType,
    SpeakerProposal,
    Url,
    UrlType,
)
from program.utils import (
    get_speaker_availability_form_matrix,
    save_speaker_availability,
)
from rideshare.models import Ride
from shop.models import Order, Product, ProductCategory
from sponsors.models import Sponsor, SponsorTier
from teams.models import Team, TeamMember, TeamShift, TeamTask
from tickets.models import TicketType
from tokens.models import Token, TokenFind
from utils.slugs import unique_slugify
from villages.models import Village

fake = Faker()
tz = pytz.timezone("Europe/Copenhagen")
logger = logging.getLogger("bornhack.%s" % __name__)


@factory.django.mute_signals(post_save)
class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory("self.UserFactory", profile=None)
    name = factory.Faker("name")
    description = factory.Faker("text")
    public_credit_name = factory.Faker("name")
    public_credit_name_approved = True


@factory.django.mute_signals(post_save)
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    profile = factory.RelatedFactory(ProfileFactory, "user")


class EmailAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmailAddress

    primary = False
    verified = True


def output_fake_md_description():
    fake_text = "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "\n\n"
    fake_text += "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "\n\n"
    fake_text += "## " + fake.sentence(nb_words=3) + "\n"
    fake_text += "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "\n\n"
    fake_text += '![The image is not awailable](/static/img/na.jpg "not available")'
    fake_text += "\n\n"
    fake_text += "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "\n\n"
    fake_text += "* [" + fake.sentence(nb_words=3) + "](" + fake.uri() + ")\n"
    fake_text += "* [" + fake.sentence(nb_words=3) + "](" + fake.uri() + ")\n"
    return fake_text


def output_fake_description():
    fake_text = "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "* [" + fake.sentence(nb_words=3) + "](" + fake.uri() + ")\n"
    return fake_text


class SpeakerProposalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SpeakerProposal

    name = factory.Faker("name")
    email = factory.Faker("email")
    biography = output_fake_md_description()
    submission_notes = factory.Iterator(["", output_fake_description()])
    needs_oneday_ticket = factory.Iterator([True, False])


class EventProposalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EventProposal

    user = factory.Iterator(User.objects.all())
    title = factory.Faker("sentence")
    abstract = output_fake_md_description()
    allow_video_recording = factory.Iterator([True, True, True, False])
    submission_notes = factory.Iterator(["", output_fake_description()])
    use_provided_speaker_laptop = factory.Iterator([True, False])


class EventProposalUrlFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Url

    url = factory.Faker("url")
    url_type = factory.Iterator(UrlType.objects.all())


class SpeakerProposalUrlFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Url

    url = factory.Faker("url")
    url_type = factory.Iterator(UrlType.objects.all())


class Command(BaseCommand):
    args = "none"
    help = "Create mock data for development instances"

    def create_camps(self):
        self.output("Creating camps...")
        camps = [
            dict(year=2016, tagline="Initial Commit", colour="#004dff", read_only=True),
            dict(year=2017, tagline="Make Tradition", colour="#750787", read_only=True),
            dict(year=2018, tagline="scale it", colour="#008026", read_only=True),
            dict(year=2019, tagline="a new /home", colour="#ffed00", read_only=True),
            dict(year=2020, tagline="Going Viral", colour="#ff8c00", read_only=False),
            dict(year=2021, tagline="Undecided", colour="#e40303", read_only=False),
        ]

        camp_instances = []

        for camp in camps:
            year = camp["year"]
            read_only = camp["read_only"]
            camp_instances.append(
                (
                    Camp.objects.create(
                        title="BornHack {}".format(year),
                        tagline=camp["tagline"],
                        slug="bornhack-{}".format(year),
                        shortslug="bornhack-{}".format(year),
                        buildup=(
                            tz.localize(datetime(year, 8, 25, 12, 0)),
                            tz.localize(datetime(year, 8, 27, 12, 0)),
                        ),
                        camp=(
                            tz.localize(datetime(year, 8, 27, 12, 0)),
                            tz.localize(datetime(year, 9, 3, 12, 0)),
                        ),
                        teardown=(
                            tz.localize(datetime(year, 9, 3, 12, 0)),
                            tz.localize(datetime(year, 9, 5, 12, 0)),
                        ),
                        colour=camp["colour"],
                    ),
                    read_only,
                )
            )

        return camp_instances

    def create_event_routing_types(self):
        t, created = Type.objects.get_or_create(name="public_credit_name_changed")
        t, created = Type.objects.get_or_create(name="ticket_created")

    def create_users(self):
        self.output("Creating users...")

        users = {}

        for i in range(0, 16):
            username = "user{}".format(i)
            user = UserFactory.create(
                username=username, email="{}@example.com".format(username)
            )
            user.set_password(username)
            user.save()
            users[i] = user
            EmailAddressFactory.create(
                user=user, email="{}@example.com".format(username)
            )

        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin"
        )
        users["admin"] = admin
        admin.profile.name = "Administrator"
        admin.profile.description = "Default adminstrative user"
        admin.profile.public_credit_name = "Administrator"
        admin.profile.public_credit_name_approved = True
        admin.profile.save()
        EmailAddress.objects.create(
            user=admin, email="admin@example.com", verified=True, primary=True
        )

        return users

    def create_news(self):
        NewsItem.objects.create(
            title="unpublished news item", content="unpublished news body here"
        )

    def create_quickfeedback_options(self):
        options = {}
        self.output("Creating quickfeedback options")
        options["na"] = FacilityQuickFeedback.objects.create(
            feedback="N/A", icon="fas fa-times"
        )
        options["attention"] = FacilityQuickFeedback.objects.create(
            feedback="Needs attention"
        )
        options["toiletpaper"] = FacilityQuickFeedback.objects.create(
            feedback="Needs more toiletpaper", icon="fas fa-toilet-paper"
        )
        options["cleaning"] = FacilityQuickFeedback.objects.create(
            feedback="Needs cleaning", icon="fas fa-broom"
        )
        options["power"] = FacilityQuickFeedback.objects.create(
            feedback="No power", icon="fas fa-bolt"
        )
        return options

    def create_facility_types(self, camp, teams, options):
        types = {}
        self.output("Creating facility types...")
        types["toilet"] = FacilityType.objects.create(
            name="Toilets",
            description="All the toilets",
            icon="fas fa-toilet",
            marker="greyIcon",
            responsible_team=teams["shit"],
        )
        types["toilet"].quickfeedback_options.add(options["na"])
        types["toilet"].quickfeedback_options.add(options["attention"])
        types["toilet"].quickfeedback_options.add(options["toiletpaper"])
        types["toilet"].quickfeedback_options.add(options["cleaning"])

        types["power"] = FacilityType.objects.create(
            name="Power Infrastructure",
            description="Power related infrastructure, distribution points, distribution cables, and so on.",
            icon="fas fa-plug",
            marker="goldIcon",
            responsible_team=teams["power"],
        )
        types["power"].quickfeedback_options.add(options["attention"])
        types["power"].quickfeedback_options.add(options["power"])
        return types

    def create_facilities(self, facility_types):
        facilities = {}
        self.output("Creating facilities...")
        facilities["toilet1"] = Facility.objects.create(
            facility_type=facility_types["toilet"],
            name="Toilet NOC East",
            description="Toilet on the east side of the NOC building",
            location=Point(9.939783, 55.387217),
        )
        facilities["toilet2"] = Facility.objects.create(
            facility_type=facility_types["toilet"],
            name="Toilet NOC West",
            description="Toilet on the west side of the NOC building",
            location=Point(9.93967, 55.387197),
        )
        facilities["pdp1"] = Facility.objects.create(
            facility_type=facility_types["power"],
            name="PDP1",
            description="In orga area",
            location=Point(9.94079, 55.388022),
        )
        facilities["pdp2"] = Facility.objects.create(
            facility_type=facility_types["power"],
            name="PDP2",
            description="In bar area",
            location=Point(9.942036, 55.387891),
        )
        facilities["pdp3"] = Facility.objects.create(
            facility_type=facility_types["power"],
            name="PDP3",
            description="In speaker tent",
            location=Point(9.938416, 55.387109),
        )
        facilities["pdp4"] = Facility.objects.create(
            facility_type=facility_types["power"],
            name="PDP4",
            description="In food area",
            location=Point(9.940146, 55.386983),
        )
        return facilities

    def create_facility_feedbacks(self, facilities, options, users):
        self.output("Creating facility feedbacks...")
        FacilityFeedback.objects.create(
            user=users[1],
            facility=facilities["toilet1"],
            quick_feedback=options["attention"],
            comment="Something smells wrong",
            urgent=True,
        )
        FacilityFeedback.objects.create(
            user=users[2],
            facility=facilities["toilet1"],
            quick_feedback=options["toiletpaper"],
            urgent=False,
        )
        FacilityFeedback.objects.create(
            facility=facilities["toilet2"],
            quick_feedback=options["cleaning"],
            comment="This place needs cleaning please. Anonymous feedback.",
            urgent=False,
        )
        FacilityFeedback.objects.create(
            facility=facilities["pdp1"],
            quick_feedback=options["attention"],
            comment="Rain cover needs some work, and we need more free plugs! This feedback is submitted anonymously.",
            urgent=False,
        )
        FacilityFeedback.objects.create(
            user=users[5],
            facility=facilities["pdp2"],
            quick_feedback=options["power"],
            comment="No power, please help",
            urgent=True,
        )

    def create_event_types(self):
        types = {}
        self.output("Creating event types...")
        types["workshop"] = EventType.objects.create(
            name="Workshop",
            slug="workshop",
            color="#ff9900",
            light_text=False,
            public=True,
            description="Workshops actively involve the participants in the learning experience",
            icon="toolbox",
            host_title="Host",
            event_duration_minutes="180",
            support_autoscheduling=True,
            support_speaker_event_conflicts=True,
        )

        types["talk"] = EventType.objects.create(
            name="Talk",
            slug="talk",
            color="#2D9595",
            light_text=True,
            public=True,
            description="A presentation on a stage",
            icon="chalkboard-teacher",
            host_title="Speaker",
            event_duration_minutes="60",
            support_autoscheduling=True,
            support_speaker_event_conflicts=True,
        )

        types["lightning"] = EventType.objects.create(
            name="Lightning Talk",
            slug="lightning-talk",
            color="#ff0000",
            light_text=True,
            public=True,
            description="A short 5-10 minute presentation",
            icon="bolt",
            host_title="Speaker",
            event_duration_minutes="5",
            support_speaker_event_conflicts=True,
        )

        types["music"] = EventType.objects.create(
            name="Music Act",
            slug="music",
            color="#1D0095",
            light_text=True,
            public=True,
            description="A musical performance",
            icon="music",
            host_title="Artist",
            event_duration_minutes="180",
            support_autoscheduling=True,
            support_speaker_event_conflicts=True,
        )

        types["keynote"] = EventType.objects.create(
            name="Keynote",
            slug="keynote",
            color="#FF3453",
            light_text=True,
            description="A keynote presentation",
            icon="star",
            host_title="Speaker",
            event_duration_minutes="90",
            support_autoscheduling=True,
            support_speaker_event_conflicts=True,
        )

        types["debate"] = EventType.objects.create(
            name="Debate",
            slug="debate",
            color="#F734C3",
            light_text=True,
            description="A panel debate with invited guests",
            icon="users",
            host_title="Guest",
            public=True,
            event_duration_minutes="120",
            support_autoscheduling=True,
            support_speaker_event_conflicts=True,
        )

        types["facility"] = EventType.objects.create(
            name="Facilities",
            slug="facilities",
            color="#cccccc",
            light_text=False,
            include_in_event_list=False,
            description="Events involving facilities like bathrooms, food area and so on",
            icon="home",
            host_title="Host",
            event_duration_minutes="720",
            support_speaker_event_conflicts=False,
        )

        types["slack"] = EventType.objects.create(
            name="Recreational",
            slug="recreational",
            color="#0000ff",
            light_text=True,
            public=True,
            description="Events of a recreational nature",
            icon="dice",
            host_title="Host",
            event_duration_minutes="60",
            support_autoscheduling=False,
            support_speaker_event_conflicts=True,
        )

        return types

    def create_url_types(self):
        self.output("Creating UrlType objects...")
        t, created = UrlType.objects.get_or_create(
            name="Other", defaults={"icon": "fas fa-link"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Homepage", defaults={"icon": "fas fa-link"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Slides", defaults={"icon": "fas fa-chalkboard-teacher"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Twitter", defaults={"icon": "fab fa-twitter"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Mastodon", defaults={"icon": "fab fa-mastodon"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Facebook", defaults={"icon": "fab fa-facebook"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Project", defaults={"icon": "fas fa-link"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Blog", defaults={"icon": "fas fa-link"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Github", defaults={"icon": "fab fa-github"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Keybase", defaults={"icon": "fab fa-keybase"}
        )
        t, created = UrlType.objects.get_or_create(
            name="Recording", defaults={"icon": "fas fa-film"}
        )

    def create_product_categories(self):
        categories = {}
        self.output("Creating productcategories...")
        categories["transportation"] = ProductCategory.objects.create(
            name="Transportation", slug="transportation"
        )
        categories["merchandise"] = ProductCategory.objects.create(
            name="Merchandise", slug="merchandise"
        )
        categories["tickets"] = ProductCategory.objects.create(
            name="Tickets", slug="tickets"
        )
        categories["villages"] = ProductCategory.objects.create(
            name="Villages", slug="villages"
        )

        return categories

    def create_global_products(self, categories):
        products = {}
        self.output("Creating global products...")
        name = "PROSA bus transport (PROSA members only)"
        products["product0"] = Product.objects.create(
            name=name,
            category=categories["transportation"],
            price=125,
            description="PROSA is sponsoring a bustrip from Copenhagen to the venue and back.",
            available_in=(
                tz.localize(datetime(2017, 3, 1, 11, 0)),
                tz.localize(datetime(2017, 10, 30, 11, 30)),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["transportation"]
                ).values_list("slug", flat=True),
            ),
        )

        name = "PROSA bus transport (open for everyone)"
        products["product1"] = Product.objects.create(
            name=name,
            category=categories["transportation"],
            price=125,
            description="PROSA is sponsoring a bustrip from Copenhagen to the venue and back.",
            available_in=(
                tz.localize(datetime(2017, 3, 1, 11, 0)),
                tz.localize(datetime(2017, 10, 30, 11, 30)),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["transportation"]
                ).values_list("slug", flat=True),
            ),
        )

        name = "T-shirt (large)"
        products["product2"] = Product.objects.create(
            name=name,
            category=categories["merchandise"],
            price=160,
            description="Get a nice t-shirt",
            available_in=(
                tz.localize(datetime(2017, 3, 1, 11, 0)),
                tz.localize(datetime(2017, 10, 30, 11, 30)),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["merchandise"]
                ).values_list("slug", flat=True),
            ),
        )

        name = "Village tent 3x3 meters, no floor"
        products["tent1"] = Product.objects.create(
            name=name,
            description="A description of the tent goes here",
            price=3325,
            category=categories["villages"],
            available_in=(
                tz.localize(datetime(2017, 3, 1, 12, 0)),
                tz.localize(datetime(2017, 8, 20, 12, 0)),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["villages"]
                ).values_list("slug", flat=True),
            ),
        )

        name = "Village tent 3x3 meters, with floor"
        products["tent2"] = Product.objects.create(
            name=name,
            description="A description of the tent goes here",
            price=3675,
            category=categories["villages"],
            available_in=(
                tz.localize(datetime(2017, 3, 1, 12, 0)),
                tz.localize(datetime(2017, 8, 20, 12, 0)),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["villages"]
                ).values_list("slug", flat=True),
            ),
        )

        return products

    def create_camp_ticket_types(self, camp):
        types = {}
        self.output("Creating tickettypes for {}...".format(camp.camp.lower.year))
        types["adult_full_week"] = TicketType.objects.create(
            name="Adult Full Week", camp=camp
        )
        types["adult_one_day"] = TicketType.objects.create(
            name="Adult One Day", camp=camp
        )
        types["child_full_week"] = TicketType.objects.create(
            name="Child Full Week", camp=camp
        )
        types["child_one_day"] = TicketType.objects.create(
            name="Child One Day", camp=camp
        )

        return types

    def create_camp_products(self, camp, categories, ticket_types):
        products = {}
        year = camp.camp.lower.year
        name = "BornHack {} Standard ticket".format(year)
        products["ticket1"] = Product.objects.create(
            name=name,
            description="A ticket",
            price=1200,
            category=categories["tickets"],
            available_in=(
                tz.localize(datetime(year, 1, 1, 12, 0)),
                tz.localize(datetime(year, 12, 20, 12, 0)),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["tickets"]
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["adult_full_week"],
        )

        name = "BornHack {} Hacker ticket".format(year)
        products["ticket2"] = Product.objects.create(
            name=name,
            description="Another ticket",
            price=1337,
            category=categories["tickets"],
            available_in=(
                tz.localize(datetime(year, 1, 1, 12, 0)),
                tz.localize(datetime(year, 12, 20, 12, 0)),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["tickets"]
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["adult_full_week"],
        )

        return products

    def create_orders(self, users, global_products, camp_products):
        orders = {}
        self.output("Creating orders...")
        orders[0] = Order.objects.create(
            user=users[1], payment_method="cash", open=None, paid=True
        )
        orders[0].orderproductrelation_set.create(
            product=camp_products["ticket1"], quantity=1
        )
        orders[0].orderproductrelation_set.create(
            product=global_products["tent1"], quantity=1
        )
        orders[0].mark_as_paid(request=None)

        orders[1] = Order.objects.create(
            user=users[2], payment_method="cash", open=None
        )
        orders[1].orderproductrelation_set.create(
            product=camp_products["ticket1"], quantity=1
        )
        orders[1].orderproductrelation_set.create(
            product=global_products["tent2"], quantity=1
        )
        orders[1].mark_as_paid(request=None)

        orders[2] = Order.objects.create(
            user=users[3], payment_method="cash", open=None
        )
        orders[2].orderproductrelation_set.create(
            product=camp_products["ticket2"], quantity=1
        )
        orders[2].orderproductrelation_set.create(
            product=camp_products["ticket1"], quantity=1
        )
        orders[2].orderproductrelation_set.create(
            product=global_products["tent2"], quantity=1
        )
        orders[2].mark_as_paid(request=None)

        orders[3] = Order.objects.create(
            user=users[4], payment_method="cash", open=None
        )
        orders[3].orderproductrelation_set.create(
            product=global_products["product0"], quantity=1
        )
        orders[3].orderproductrelation_set.create(
            product=camp_products["ticket2"], quantity=1
        )
        orders[3].orderproductrelation_set.create(
            product=global_products["tent1"], quantity=1
        )
        orders[3].mark_as_paid(request=None)

        return orders

    def create_camp_tracks(self, camp):
        tracks = {}
        year = camp.camp.lower.year
        self.output("Creating event_tracks for {}...".format(year))
        tracks[1] = EventTrack.objects.create(
            camp=camp, name="BornHack", slug=camp.slug
        )

        return tracks

    def create_event_locations(self, camp):
        locations = {}
        year = camp.camp.lower.year
        self.output("Creating event_locations for {}...".format(year))
        locations["speakers_tent"] = EventLocation.objects.create(
            name="Speakers Tent",
            slug="speakers-tent",
            icon="comment",
            camp=camp,
            capacity=150,
        )
        locations["workshop_room_1"] = EventLocation.objects.create(
            name="Workshop room 1 (big)",
            slug="workshop-room-1",
            icon="briefcase",
            camp=camp,
            capacity=50,
        )
        locations["workshop_room_2"] = EventLocation.objects.create(
            name="Workshop room 2 (small)",
            slug="workshop-room-2",
            icon="briefcase",
            camp=camp,
            capacity=25,
        )
        locations["workshop_room_3"] = EventLocation.objects.create(
            name="Workshop room 3 (small)",
            slug="workshop-room-3",
            icon="briefcase",
            camp=camp,
            capacity=25,
        )
        locations["bar_area"] = EventLocation.objects.create(
            name="Bar Area",
            slug="bar-area",
            icon="glass-cheers",
            camp=camp,
            capacity=50,
        )
        locations["food_area"] = EventLocation.objects.create(
            name="Food Area", slug="food-area", icon="utensils", camp=camp, capacity=50,
        )
        locations["infodesk"] = EventLocation.objects.create(
            name="Infodesk", slug="infodesk", icon="info", camp=camp, capacity=20,
        )

        # add workshop room conflicts (the big root can not be used while either
        # of the small rooms are in use, and vice versa)
        locations["workshop_room_1"].conflicts.add(locations["workshop_room_2"])
        locations["workshop_room_1"].conflicts.add(locations["workshop_room_3"])

        return locations

    def create_camp_news(self, camp):
        year = camp.camp.lower.year
        self.output("Creating news for {}...".format(year))
        NewsItem.objects.create(
            title="Welcome to {}".format(camp.title),
            content="news body here with <b>html</b> support",
            published_at=tz.localize(datetime(year, 8, 27, 12, 0)),
        )
        NewsItem.objects.create(
            title="{} is over".format(camp.title),
            content="news body here",
            published_at=tz.localize(datetime(year, 9, 4, 12, 0)),
        )

    def create_camp_event_sessions(self, camp, event_types, event_locations):
        self.output(f"Creating EventSessions for {camp}...")
        days = camp.get_days(camppart="camp")[1:-1]
        for day in days:
            start = day.lower
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["talk"],
                event_location=event_locations["speakers_tent"],
                when=(
                    tz.localize(datetime(start.year, start.month, start.day, 11, 0)),
                    tz.localize(datetime(start.year, start.month, start.day, 18, 0)),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["slack"],
                event_location=event_locations["speakers_tent"],
                when=(
                    tz.localize(datetime(start.year, start.month, start.day, 12, 0)),
                    tz.localize(datetime(start.year, start.month, start.day, 13, 0)),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["music"],
                event_location=event_locations["bar_area"],
                when=(
                    tz.localize(datetime(start.year, start.month, start.day, 22, 0)),
                    tz.localize(datetime(start.year, start.month, start.day, 22, 0))
                    + timedelta(hours=3),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["workshop"],
                event_location=event_locations["workshop_room_1"],
                when=(
                    tz.localize(datetime(start.year, start.month, start.day, 12, 0)),
                    tz.localize(datetime(start.year, start.month, start.day, 18, 0)),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["workshop"],
                event_location=event_locations["workshop_room_2"],
                when=(
                    tz.localize(datetime(start.year, start.month, start.day, 12, 0)),
                    tz.localize(datetime(start.year, start.month, start.day, 18, 0)),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["workshop"],
                event_location=event_locations["workshop_room_3"],
                when=(
                    tz.localize(datetime(start.year, start.month, start.day, 12, 0)),
                    tz.localize(datetime(start.year, start.month, start.day, 18, 0)),
                ),
            )
        # create sessions for the keynotes
        for day in [days[1], days[3], days[5]]:
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["keynote"],
                event_location=event_locations["speakers_tent"],
                when=(
                    tz.localize(
                        datetime(day.lower.year, day.lower.month, day.lower.day, 20, 0)
                    ),
                    tz.localize(
                        datetime(day.lower.year, day.lower.month, day.lower.day, 21, 30)
                    ),
                ),
            )

    def create_camp_proposals(self, camp, event_types):
        year = camp.camp.lower.year
        self.output("Creating event- and speaker_proposals for {}...".format(year))

        # add 45 talks
        talkproposals = EventProposalFactory.create_batch(
            45,
            track=factory.Iterator(camp.event_tracks.all()),
            event_type=event_types["talk"],
        )
        # and 15 workshops
        workshopproposals = EventProposalFactory.create_batch(
            15,
            track=factory.Iterator(camp.event_tracks.all()),
            event_type=event_types["workshop"],
        )
        # and 3 keynotes
        # (in the real world these are submitted as talks
        # and promoted to keynotes by the content team)
        keynoteproposals = EventProposalFactory.create_batch(
            3,
            track=factory.Iterator(camp.event_tracks.all()),
            event_type=event_types["keynote"],
        )

        tags = [
            "infosec",
            "hardware",
            "politics",
            "django",
            "development",
            "games",
            "privacy",
            "vampires",
            "linux",
        ]

        for ep in talkproposals + workshopproposals + keynoteproposals:
            # create a speakerproposal for this EventProposal
            sp = SpeakerProposalFactory(camp=camp, user=ep.user)
            ep.speakers.add(sp)
            # 20% chance we add an extra speaker
            if random.randint(1, 10) > 8:
                other_speakers = SpeakerProposal.objects.filter(camp=camp).exclude(
                    uuid=sp.uuid
                )
                # ... if we have any...
                if other_speakers.exists():
                    # add an extra speaker
                    ep.speakers.add(random.choice(other_speakers))

            # add tags for 2 out of 3 events
            if random.choice([True, True, False]):
                # add 1-3 tags for this EP
                ep.tags.add(*random.sample(tags, k=random.randint(1, 3)))

        EventProposal.objects.create(
            user=random.choice(User.objects.all()),
            title="Lunch break",
            abstract="Daily lunch break. Remember to drink water.",
            event_type=event_types["slack"],
            track=random.choice(camp.event_tracks.all()),
        ).mark_as_approved()

    def create_proposal_urls(self, camp):
        """ Create URL objects for the proposals """
        year = camp.camp.lower.year
        self.output(
            "Creating URLs for Speaker- and EventProposals for {}...".format(year)
        )
        SpeakerProposalUrlFactory.create_batch(
            100,
            speaker_proposal=factory.Iterator(
                SpeakerProposal.objects.filter(camp=camp)
            ),
        )
        EventProposalUrlFactory.create_batch(
            100,
            event_proposal=factory.Iterator(
                EventProposal.objects.filter(track__camp=camp)
            ),
        )

    def generate_speaker_availability(self, camp):
        """ Create SpeakerAvailability objects for the SpeakerProposals """
        year = camp.camp.lower.year
        self.output(
            "Generating random SpeakerProposalAvailability for {}...".format(year)
        )
        for sp in camp.speaker_proposals.all():
            # generate a matrix for this speaker_proposals event_types
            matrix = get_speaker_availability_form_matrix(
                sessions=sp.camp.event_sessions.filter(
                    event_type__in=sp.event_types.all(),
                )
            )

            # build a "form" object so we can reuse save_speaker_availability()
            class FakeForm:
                cleaned_data = {}

            form = FakeForm()
            for date, daychunks in matrix.items():
                # 90% chance we have info for any given day
                if random.randint(1, 100) > 90:
                    # no availability info for this entire day, sorry
                    continue
                for daychunk, data in daychunks.items():
                    if not data:
                        continue
                    # 90% chance this speaker is available for any given chunk
                    form.cleaned_data[data["fieldname"]] = random.randint(1, 100) < 90
            # print(f"saving availability for speaker {sp}: {form.cleaned_data}")
            save_speaker_availability(form, sp)

    def approve_speaker_proposals(self, camp):
        """ Approve all keynotes but reject 10% of other events """
        for sp in camp.speaker_proposals.filter(
            event_proposals__event_type__name="Keynote"
        ):
            sp.mark_as_approved()

        for sp in camp.speaker_proposals.filter(proposal_status="pending"):
            # we do not approve all speakers
            x = random.randint(1, 100)
            if x < 90:
                sp.mark_as_approved()
            elif x < 95:
                # leave this as pending
                continue
            else:
                sp.mark_as_rejected()

    def approve_event_proposals(self, camp):
        for ep in camp.event_proposals.filter(proposal_status="pending"):
            # are all speakers for this event approved?
            for sp in ep.speakers.all():
                if not hasattr(sp, "speaker"):
                    break
            else:
                # all speakers are approved, approve the event? always approve keynotes!
                if random.randint(1, 100) < 90 or ep.event_type.name == "Keynote":
                    ep.mark_as_approved()
                else:
                    ep.mark_as_rejected()

        # set demand for workshops to see the autoscheduler in action
        for event in camp.events.filter(event_type__name="Workshop"):
            # this should put about half the workshops in the big room
            # (since the small rooms have max. 25 ppl capacity)
            event.demand = random.randint(10, 40)
            event.save()

    def create_camp_scheduling(self, camp):
        year = camp.camp.lower.year
        self.output("Creating scheduling for {}...".format(year))

        # create a lunchbreak daily in speakers tent
        lunch = Event.objects.get(track__camp=camp, title="Lunch break")
        for day in camp.get_days(camppart="camp")[1:-1]:
            date = day.lower.date()
            start = tz.localize(datetime(date.year, date.month, date.day, 12, 0))
            lunchslot = EventSlot.objects.get(
                event_session__event_location=camp.event_locations.get(
                    name="Speakers Tent"
                ),
                event_session__event_type=EventType.objects.get(name="Recreational"),
                when=(start, start + timedelta(hours=1)),
            )
            lunchslot.event = lunch
            lunchslot.autoscheduled = False
            lunchslot.save()

        # exercise the autoscheduler a bit
        scheduler = AutoScheduler(camp=camp)
        schedulestart = timezone.now()
        try:
            autoschedule = scheduler.calculate_autoschedule()
            if autoschedule:
                scheduler.apply(autoschedule)
        except ValueError as E:
            self.output(f"Got exception while calculating autoschedule: {E}")
        scheduleduration = timezone.now() - schedulestart
        self.output(
            f"Done running autoscheduler for {year}... It took {scheduleduration}"
        )

    def create_camp_speaker_event_conflicts(self, camp):
        year = camp.camp.lower.year
        self.output(
            "Generating event_conflicts for SpeakerProposals for {}...".format(year)
        )
        # loop over all
        for sp in camp.speaker_proposals.all():
            # not all speakers add conflicts
            if random.choice([True, True, False]):
                # pick 0-10 events this speaker wants to attend
                conflictcount = random.randint(0, 10)
                sp.event_conflicts.set(
                    Event.objects.filter(
                        track__camp=camp,
                        event_type__support_speaker_event_conflicts=True,
                    ).order_by("?")[0:conflictcount]
                )

    def create_camp_rescheduling(self, camp):
        year = camp.camp.lower.year
        # reapprove all speaker_proposals so the new availability takes effect
        for prop in camp.speaker_proposals.filter(proposal_status="approved"):
            prop.mark_as_approved()
        # exercise the autoscheduler a bit
        self.output("Rescheduling {}...".format(year))
        scheduler = AutoScheduler(camp=camp)
        schedulestart = timezone.now()
        try:
            autoschedule, diff = scheduler.calculate_similar_autoschedule()
            scheduler.apply(autoschedule)
        except ValueError as E:
            self.output(f"Got exception while calculating similar autoschedule: {E}")
            autoschedule = None
        scheduleduration = timezone.now() - schedulestart
        self.output(f"Done rescheduling for {year}... It took {scheduleduration}.")

    def create_camp_villages(self, camp, users):
        year = camp.camp.lower.year
        self.output("Creating villages for {}...".format(year))
        Village.objects.create(
            contact=users[1],
            camp=camp,
            name="Baconsvin",
            slug="baconsvin",
            description="The camp with the doorbell-pig! Baconsvin is a group of happy people from Denmark doing a lot of open source, and are always happy to talk about infosec, hacking, BSD, and much more. A lot of the organizers of BornHack live in Baconsvin village. Come by and squeeze the pig and sign our guestbook!",
        )
        Village.objects.create(
            contact=users[2],
            camp=camp,
            name="NetworkWarriors",
            slug="networkwarriors",
            description="We will have a tent which house the NOC people, various lab equipment people can play with, and have fun. If you want to talk about networking, come by, and if you have trouble with the Bornhack network contact us.",
        )
        Village.objects.create(
            contact=users[3],
            camp=camp,
            name="TheCamp.dk",
            slug="the-camp",
            description="This village is representing TheCamp.dk, an annual danish tech camp held in July. The official subjects for this event is open source software, network and security. In reality we are interested in anything from computers to illumination soap bubbles and irish coffee",
        )

    def create_camp_teams(self, camp):
        teams = {}
        year = camp.camp.lower.year
        self.output("Creating teams for {}...".format(year))
        teams["orga"] = Team.objects.create(
            name="Orga",
            description="The Orga team are the main organisers. All tasks are Orga responsibility until they are delegated to another team",
            camp=camp,
            needs_members=False,
            permission_set="orgateam_permission",
        )
        teams["noc"] = Team.objects.create(
            name="NOC",
            description="The NOC team is in charge of establishing and running a network onsite.",
            camp=camp,
            permission_set="nocteam_permission",
        )
        teams["bar"] = Team.objects.create(
            name="Bar",
            description="The Bar team plans, builds and run the IRL bar!",
            camp=camp,
            permission_set="barteam_permission",
        )
        teams["shuttle"] = Team.objects.create(
            name="Shuttle",
            description="The shuttle team drives people to and from the trainstation or the supermarket",
            camp=camp,
            permission_set="shuttleteam_permission",
        )
        teams["power"] = Team.objects.create(
            name="Power",
            description="The power team makes sure we have power all over the venue",
            camp=camp,
            permission_set="powerteam_permission",
        )
        teams["shit"] = Team.objects.create(
            name="Sanitation",
            description="Team shit takes care of the toilets",
            camp=camp,
            permission_set="sanitationteam_permission",
        )

        return teams

    def create_camp_team_tasks(self, camp, teams):
        year = camp.camp.lower.year
        self.output("Creating TeamTasks for {}...".format(year))
        TeamTask.objects.create(
            team=teams["noc"],
            name="Setup private networks",
            description="All the private networks need to be setup",
        )
        TeamTask.objects.create(
            team=teams["noc"],
            name="Setup public networks",
            description="All the public networks need to be setup",
        )
        TeamTask.objects.create(
            team=teams["noc"],
            name="Deploy access points",
            description="All access points need to be deployed",
        )
        TeamTask.objects.create(
            team=teams["noc"],
            name="Deploy fiber cables",
            description="We need the fiber deployed where necessary",
        )
        TeamTask.objects.create(
            team=teams["bar"],
            name="List of booze",
            description="A list of the different booze we need to have in the bar durng bornhack",
        )
        TeamTask.objects.create(
            team=teams["bar"],
            name="Chairs",
            description="We need a solution for chairs",
        )
        TeamTask.objects.create(
            team=teams["bar"], name="Taps", description="Taps must be ordered"
        )
        TeamTask.objects.create(
            team=teams["bar"],
            name="Coffee",
            description="We need to get some coffee for our coffee machine",
        )
        TeamTask.objects.create(
            team=teams["bar"],
            name="Ice",
            description="We need ice cubes and crushed ice in the bar",
        )

    def create_camp_team_memberships(self, camp, teams, users):
        memberships = {}
        year = camp.camp.lower.year
        self.output("Creating team memberships for {}...".format(year))
        # noc team
        memberships["noc"] = {}
        memberships["noc"]["user4"] = TeamMember.objects.create(
            team=teams["noc"], user=users[4], approved=True, responsible=True
        )
        memberships["noc"]["user1"] = TeamMember.objects.create(
            team=teams["noc"], user=users[1], approved=True
        )
        memberships["noc"]["user5"] = TeamMember.objects.create(
            team=teams["noc"], user=users[5], approved=True
        )
        memberships["noc"]["user2"] = TeamMember.objects.create(
            team=teams["noc"], user=users[2]
        )

        # bar team
        memberships["bar"] = {}
        memberships["bar"]["user1"] = TeamMember.objects.create(
            team=teams["bar"], user=users[1], approved=True, responsible=True
        )
        memberships["bar"]["user3"] = TeamMember.objects.create(
            team=teams["bar"], user=users[3], approved=True, responsible=True
        )
        memberships["bar"]["user2"] = TeamMember.objects.create(
            team=teams["bar"], user=users[2], approved=True
        )
        memberships["bar"]["user7"] = TeamMember.objects.create(
            team=teams["bar"], user=users[7], approved=True
        )
        memberships["bar"]["user8"] = TeamMember.objects.create(
            team=teams["bar"], user=users[8]
        )

        # orga team
        memberships["orga"] = {}
        memberships["orga"]["user1"] = TeamMember.objects.create(
            team=teams["orga"], user=users[1], approved=True, responsible=True
        )
        memberships["orga"]["user3"] = TeamMember.objects.create(
            team=teams["orga"], user=users[3], approved=True, responsible=True
        )
        memberships["orga"]["user8"] = TeamMember.objects.create(
            team=teams["orga"], user=users[8], approved=True, responsible=True
        )
        memberships["orga"]["user9"] = TeamMember.objects.create(
            team=teams["orga"], user=users[9], approved=True, responsible=True
        )
        memberships["orga"]["user4"] = TeamMember.objects.create(
            team=teams["orga"], user=users[4], approved=True, responsible=True
        )

        # shuttle team
        memberships["shuttle"] = {}
        memberships["shuttle"]["user7"] = TeamMember.objects.create(
            team=teams["shuttle"], user=users[7], approved=True, responsible=True
        )
        memberships["shuttle"]["user3"] = TeamMember.objects.create(
            team=teams["shuttle"], user=users[3], approved=True
        )
        memberships["shuttle"]["user9"] = TeamMember.objects.create(
            team=teams["shuttle"], user=users[9]
        )

        return memberships

    def create_camp_team_shifts(self, camp, teams, team_memberships):
        shifts = {}
        year = camp.camp.lower.year
        self.output("Creating team shifts for {}...".format(year))
        shifts[0] = TeamShift.objects.create(
            team=teams["shuttle"],
            shift_range=(
                tz.localize(datetime(year, 8, 27, 2, 0)),
                tz.localize(datetime(year, 8, 27, 8, 0)),
            ),
            people_required=1,
        )
        shifts[0].team_members.add(team_memberships["shuttle"]["user7"])
        shifts[1] = TeamShift.objects.create(
            team=teams["shuttle"],
            shift_range=(
                tz.localize(datetime(year, 8, 27, 8, 0)),
                tz.localize(datetime(year, 8, 27, 14, 0)),
            ),
            people_required=1,
        )
        shifts[2] = TeamShift.objects.create(
            team=teams["shuttle"],
            shift_range=(
                tz.localize(datetime(year, 8, 27, 14, 0)),
                tz.localize(datetime(year, 8, 27, 20, 0)),
            ),
            people_required=1,
        )

    def create_camp_info_categories(self, camp, teams):
        categories = {}
        year = camp.camp.lower.year
        self.output("Creating infocategories for {}...".format(year))
        categories["when"] = InfoCategory.objects.create(
            team=teams["orga"], headline="When is BornHack happening?", anchor="when"
        )
        categories["travel"] = InfoCategory.objects.create(
            team=teams["orga"], headline="Travel Information", anchor="travel"
        )
        categories["sleep"] = InfoCategory.objects.create(
            team=teams["orga"], headline="Where do I sleep?", anchor="sleep"
        )

        return categories

    def create_camp_info_items(self, camp, categories):
        year = camp.camp.lower.year
        self.output("Creating infoitems for {}...".format(year))
        InfoItem.objects.create(
            category=categories["when"],
            headline="Opening",
            anchor="opening",
            body="BornHack {} starts saturday, august 27th, at noon (12:00). It will be possible to access the venue before noon if for example you arrive early in the morning with the ferry. But please dont expect everything to be ready before noon :)".format(
                year
            ),
        )
        InfoItem.objects.create(
            category=categories["when"],
            headline="Closing",
            anchor="closing",
            body="BornHack {} ends saturday, september 3rd, at noon (12:00). Rented village tents must be empty and cleaned at this time, ready to take down. Participants must leave the site no later than 17:00 on the closing day (or stay and help us clean up).".format(
                year
            ),
        )
        InfoItem.objects.create(
            category=categories["travel"],
            headline="Public Transportation",
            anchor="public-transportation",
            body=output_fake_md_description(),
        )
        InfoItem.objects.create(
            category=categories["travel"],
            headline="Bus to and from BornHack",
            anchor="bus-to-and-from-bornhack",
            body="PROSA, the union of IT-professionals in Denmark, has set up a great deal for BornHack attendees travelling from Copenhagen to BornHack. For only 125kr, about 17 euros, you can be transported to the camp on opening day, and back to Copenhagen at the end of the camp!",
        )
        InfoItem.objects.create(
            category=categories["when"],
            headline="Driving and Parking",
            anchor="driving-and-parking",
            body=output_fake_md_description(),
        )
        InfoItem.objects.create(
            category=categories["sleep"],
            headline="Camping",
            anchor="camping",
            body="BornHack is first and foremost a tent camp. You need to bring a tent to sleep in. Most people go with some friends and make a camp somewhere at the venue. See also the section on Villages - you might be able to find some likeminded people to camp with.",
        )
        InfoItem.objects.create(
            category=categories["sleep"],
            headline="Cabins",
            anchor="cabins",
            body="We rent out a few cabins at the venue with 8 beds each for people who don't want to sleep in tents for some reason. A tent is the cheapest sleeping option (you just need a ticket), but the cabins are there if you want them.",
        )

    def create_camp_feedback(self, camp, users):
        year = camp.camp.lower.year
        self.output("Creating feedback for {}...".format(year))
        Feedback.objects.create(
            camp=camp, user=users[1], feedback="Awesome event, will be back next year"
        )
        Feedback.objects.create(
            camp=camp,
            user=users[3],
            feedback="Very nice, though a bit more hot water would be awesome",
        )
        Feedback.objects.create(
            camp=camp, user=users[5], feedback="Is there a token here?"
        )
        Feedback.objects.create(
            camp=camp, user=users[9], feedback="That was fun. Thanks!"
        )

    def create_camp_rides(self, camp, users):
        year = camp.camp.lower.year
        self.output("Creating rides for {}...".format(year))
        Ride.objects.create(
            camp=camp,
            user=users[1],
            seats=2,
            from_location="Copenhagen",
            to_location="BornHack",
            when=tz.localize(datetime(year, 8, 27, 12, 0)),
            description="I have space for two people and a little bit of luggage",
        )
        Ride.objects.create(
            camp=camp,
            user=users[1],
            seats=2,
            from_location="BornHack",
            to_location="Copenhagen",
            when=tz.localize(datetime(year, 9, 4, 12, 0)),
            description="I have space for two people and a little bit of luggage",
        )
        Ride.objects.create(
            camp=camp,
            user=users[4],
            seats=1,
            from_location="Aarhus",
            to_location="BornHack",
            when=tz.localize(datetime(year, 8, 27, 12, 0)),
            description="I need a ride and have a large backpack",
        )

    def create_camp_cfp(self, camp):
        year = camp.camp.lower.year
        self.output("Creating CFP for {}...".format(year))
        camp.call_for_participation_open = True
        camp.call_for_participation = "Please give a talk at Bornhack {}...".format(
            year
        )
        camp.save()

    def create_camp_cfs(self, camp):
        year = camp.camp.lower.year
        self.output("Creating CFS for {}...".format(year))
        camp.call_for_sponsors_open = True
        camp.call_for_sponsors = "Please give us ALL the money so that we can make Bornhack {} the best ever!".format(
            year
        )
        camp.save()

    def create_camp_sponsor_tiers(self, camp):
        tiers = {}
        year = camp.camp.lower.year
        self.output("Creating sponsor tiers for {}...".format(year))
        tiers["platinum"] = SponsorTier.objects.create(
            name="Platinum sponsors",
            description="- 10 tickets\n- logo on website\n- physical banner in the speaker's tent\n- thanks from the podium\n- recruitment area\n- sponsor meeting with organizers\n- promoted HackMe\n- sponsored social event",
            camp=camp,
            weight=0,
            tickets=10,
        )
        tiers["gold"] = SponsorTier.objects.create(
            name="Gold sponsors",
            description="- 10 tickets\n- logo on website\n- physical banner in the speaker's tent\n- thanks from the podium\n- recruitment area\n- sponsor meeting with organizers\n- promoted HackMe",
            camp=camp,
            weight=1,
            tickets=10,
        )
        tiers["silver"] = SponsorTier.objects.create(
            name="Silver sponsors",
            description="- 5 tickets\n- logo on website\n- physical banner in the speaker's tent\n- thanks from the podium\n- recruitment area\n- sponsor meeting with organizers",
            camp=camp,
            weight=2,
            tickets=5,
        )
        tiers["sponsor"] = SponsorTier.objects.create(
            name="Sponsors",
            description="- 2 tickets\n- logo on website\n- physical banner in the speaker's tent\n- thanks from the podium\n- recruitment area",
            camp=camp,
            weight=3,
            tickets=2,
        )

        return tiers

    def create_camp_sponsors(self, camp, tiers):
        year = camp.camp.lower.year
        self.output("Creating sponsors for {}...".format(year))
        Sponsor.objects.create(
            name="PROSA",
            tier=tiers["platinum"],
            description="Bus Trip",
            logo_filename="PROSA-logo.png",
            url="https://www.prosa.dk",
        )
        Sponsor.objects.create(
            name="DKUUG",
            tier=tiers["platinum"],
            description="Speakers tent",
            logo_filename="DKUUGlogo.jpeg",
            url="http://www.dkuug.dk/",
        )
        Sponsor.objects.create(
            name="LetsGo",
            tier=tiers["silver"],
            description="Shuttle",
            logo_filename="letsgo.png",
            url="https://letsgo.dk",
        )
        Sponsor.objects.create(
            name="Saxo Bank",
            tier=tiers["gold"],
            description="Cash Sponsorship",
            logo_filename="saxobank.png",
            url="https://home.saxo",
        )
        Sponsor.objects.create(
            name="CSIS",
            tier=tiers["sponsor"],
            description="Cash Sponsorship",
            logo_filename="CSIS_PRI_LOGO_TURQUOISE_RGB.jpg",
            url="https://csis.dk",
        )

    def create_camp_tokens(self, camp):
        tokens = {}
        year = camp.camp.lower.year
        self.output("Creating tokens for {}...".format(year))
        tokens[0] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category="Physical",
            description="Token in the back of the speakers tent (in binary)",
        )
        tokens[1] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category="Internet",
            description="Twitter",
        )
        tokens[2] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category="Website",
            description="Token hidden in the X-Secret-Token HTTP header on the BornHack website",
        )
        tokens[3] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category="Physical",
            description="Token in infodesk (QR code)",
        )
        tokens[4] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category="Physical",
            description="Token on the back of the BornHack {} badge".format(year),
        )
        tokens[5] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category="Website",
            description="Token hidden in EXIF data in the logo posted on the website sunday",
        )

        return tokens

    def create_camp_token_finds(self, camp, tokens, users):
        year = camp.camp.lower.year
        self.output("Creating token finds for {}...".format(year))
        TokenFind.objects.create(token=tokens[3], user=users[4])
        TokenFind.objects.create(token=tokens[5], user=users[4])
        TokenFind.objects.create(token=tokens[2], user=users[7])
        TokenFind.objects.create(token=tokens[1], user=users[3])
        TokenFind.objects.create(token=tokens[4], user=users[2])
        TokenFind.objects.create(token=tokens[5], user=users[6])
        for i in range(0, 6):
            TokenFind.objects.create(token=tokens[i], user=users[1])

    def output(self, message):
        self.stdout.write(
            "%s: %s" % (timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message)
        )

    def handle(self, *args, **options):
        start = timezone.now()
        self.output(
            self.style.SUCCESS("----------[ Running bootstrap-devsite ]----------")
        )
        self.output(self.style.SUCCESS("----------[ Global stuff ]----------"))

        camps = self.create_camps()
        self.create_event_routing_types()
        users = self.create_users()

        self.create_news()

        event_types = self.create_event_types()

        self.create_url_types()

        product_categories = self.create_product_categories()

        global_products = self.create_global_products(product_categories)

        quickfeedback_options = self.create_quickfeedback_options()

        for (camp, read_only) in camps:
            year = camp.camp.lower.year

            self.output(
                self.style.SUCCESS("----------[ Bornhack {} ]----------".format(year))
            )

            if year < 2021:
                ticket_types = self.create_camp_ticket_types(camp)

                camp_products = self.create_camp_products(
                    camp, product_categories, ticket_types
                )

                self.create_orders(users, global_products, camp_products)

                self.create_camp_tracks(camp)

                locations = self.create_event_locations(camp)

                self.create_camp_news(camp)

                self.create_camp_cfp(camp)

                self.create_camp_proposals(camp, event_types)

                self.create_proposal_urls(camp)

                self.create_camp_event_sessions(camp, event_types, locations)

                self.generate_speaker_availability(camp)

                try:
                    self.approve_speaker_proposals(camp)
                except ValidationError:
                    self.output(
                        "Name collision, bad luck. Run 'manage.py flush' and run the bootstrap script again!"
                    )
                    sys.exit(1)

                self.approve_event_proposals(camp)

                self.create_camp_scheduling(camp)

                # shuffle it up - delete and create new random availability
                self.generate_speaker_availability(camp)

                # and create some speaker<>event conflicts
                self.create_camp_speaker_event_conflicts(camp)

                # recalculate the autoschedule
                self.create_camp_rescheduling(camp)

                self.create_camp_villages(camp, users)

                teams = self.create_camp_teams(camp)

                self.create_camp_team_tasks(camp, teams)

                team_memberships = self.create_camp_team_memberships(camp, teams, users)

                self.create_camp_team_shifts(camp, teams, team_memberships)

                facility_types = self.create_facility_types(
                    camp, teams, quickfeedback_options
                )

                facilities = self.create_facilities(facility_types)

                self.create_facility_feedbacks(facilities, quickfeedback_options, users)

                info_categories = self.create_camp_info_categories(camp, teams)

                self.create_camp_info_items(camp, info_categories)

                self.create_camp_feedback(camp, users)

                self.create_camp_rides(camp, users)

                self.create_camp_cfs(camp)

                sponsor_tiers = self.create_camp_sponsor_tiers(camp)

                self.create_camp_sponsors(camp, sponsor_tiers)

                tokens = self.create_camp_tokens(camp)

                self.create_camp_token_finds(camp, tokens, users)
            else:
                self.output("Not creating anything for this year yet")

            camp.read_only = read_only
            camp.call_for_participation_open = not read_only
            camp.call_for_sponsors_open = not read_only
            camp.save()

        self.output("----------[ Finishing up ]----------")

        self.output("Adding event routing...")
        Routing.objects.create(
            team=teams["orga"],
            eventtype=Type.objects.get(name="public_credit_name_changed"),
        )
        Routing.objects.create(
            team=teams["orga"], eventtype=Type.objects.get(name="ticket_created")
        )

        self.output("done!")
        duration = timezone.now() - start
        self.output(f"bootstrap-devsite took {duration}!")
