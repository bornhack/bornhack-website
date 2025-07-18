"""Base class for bootstrapping testdata in the application."""

from __future__ import annotations

import logging
import random
import sys
import uuid
from datetime import datetime
from datetime import timedelta

import factory
import pytz
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import GeometryCollection
from django.contrib.gis.geos import Point
from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.crypto import get_random_string
from faker import Faker

from camps.models import Camp
from camps.models import Permission as CampPermission
from economy.factories import BankAccountFactory
from economy.factories import BankFactory
from economy.factories import BankTransactionFactory
from economy.factories import ClearhausSettlementFactory
from economy.factories import CoinifyBalanceFactory
from economy.factories import CoinifyInvoiceFactory
from economy.factories import CoinifyPaymentIntentFactory
from economy.factories import CoinifyPayoutFactory
from economy.factories import CoinifySettlementFactory
from economy.factories import CredebtorFactory
from economy.factories import EpayTransactionFactory
from economy.factories import ExpenseFactory
from economy.factories import MobilePayTransactionFactory
from economy.factories import RevenueFactory
from economy.factories import ZettleBalanceFactory
from economy.factories import ZettleReceiptFactory
from economy.models import Chain
from economy.models import Credebtor
from economy.models import Expense
from economy.models import Pos
from economy.models import Reimbursement
from events.factories import EventProposalFactory
from events.factories import EventProposalUrlFactory
from events.factories import SpeakerProposalFactory
from events.factories import SpeakerProposalUrlFactory
from events.models import Routing
from events.models import Type
from facilities.models import Facility
from facilities.models import FacilityFeedback
from facilities.models import FacilityQuickFeedback
from facilities.models import FacilityType
from feedback.models import Feedback
from info.models import InfoCategory
from info.models import InfoItem
from maps.models import Feature
from maps.models import Group as MapGroup
from maps.models import Layer
from news.models import NewsItem
from profiles.factories import EmailAddressFactory
from profiles.factories import UserFactory
from program.autoscheduler import AutoScheduler
from program.models import Event
from program.models import EventLocation
from program.models import EventProposal
from program.models import EventSession
from program.models import EventSlot
from program.models import EventTrack
from program.models import EventType
from program.models import SpeakerProposal
from program.models import UrlType
from program.utils import get_speaker_availability_form_matrix
from program.utils import save_speaker_availability
from rideshare.models import Ride
from shop.models import Order
from shop.models import Product
from shop.models import ProductCategory
from sponsors.models import Sponsor
from sponsors.models import SponsorTier
from teams.models import Team
from teams.models import TeamMember
from teams.models import TeamShift
from teams.models import TeamTask
from tickets.models import PrizeTicket
from tickets.models import SponsorTicket
from tickets.models import TicketType
from tokens.models import Token
from tokens.models import TokenCategory
from tokens.models import TokenFind
from utils.slugs import unique_slugify
from villages.models import Village

from .functions import output_fake_md_description

fake = Faker()
tz = pytz.timezone("Europe/Copenhagen")
logger = logging.getLogger(f"bornhack.{__name__}")


class Bootstrap:
    """Main bootstrap class."""

    camps: list[Camp]
    camp: Camp
    users: dict
    teams: dict
    event_types: dict
    product_categories: dict
    quickfeedback_options: dict

    def create_camps(self, camps: dict) -> None:
        """Creates all camps from a dict of camps."""
        self.output("Creating camps...")

        camp_instances = []

        for camp in camps:
            year = camp["year"]
            read_only = camp["read_only"]
            camp_instances.append(
                (
                    Camp.objects.create(
                        title=f"BornHack {year}",
                        tagline=camp["tagline"],
                        slug=f"bornhack-{year}",
                        shortslug=f"bornhack-{year}",
                        buildup=(
                            datetime(year, 8, 25, 12, 0, tzinfo=tz),
                            datetime(year, 8, 27, 12, 0, tzinfo=tz),
                        ),
                        camp=(
                            datetime(year, 8, 27, 12, 0, tzinfo=tz),
                            datetime(year, 9, 3, 12, 0, tzinfo=tz),
                        ),
                        teardown=(
                            datetime(year, 9, 3, 12, 0, tzinfo=tz),
                            datetime(year, 9, 5, 12, 0, tzinfo=tz),
                        ),
                        colour=camp["colour"],
                        light_text=camp.get("light_text", True),
                    ),
                    read_only,
                ),
            )

        self.camps = camp_instances

    def create_event_routing_types(self) -> None:
        """Create event routing types."""
        t, created = Type.objects.get_or_create(name="public_credit_name_changed")
        t, created = Type.objects.get_or_create(name="ticket_created")

    def create_users(self, amount: int) -> None:
        """Create users."""
        self.output("Creating users...")

        users = {}

        for i in range(amount):
            username = f"user{i}"
            user = UserFactory.create(
                username=str(uuid.uuid4()),
                email=f"{username}@example.com",
            )
            user.set_password(username)
            user.save()
            users[i] = user
            EmailAddressFactory.create(
                user=user,
                email=f"{username}@example.com",
                primary=True,
            )

        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin",
        )
        users["admin"] = admin
        admin.profile.name = "Administrator"
        admin.profile.description = "Default adminstrative user"
        admin.profile.public_credit_name = "Administrator"
        admin.profile.public_credit_name_approved = True
        admin.profile.save()
        EmailAddress.objects.create(
            user=admin,
            email="admin@example.com",
            verified=True,
            primary=True,
        )

        self.users = users

    def create_news(self) -> None:
        """Create fake news."""
        NewsItem.objects.create(
            title="unpublished news item",
            content="unpublished news body here",
        )

    def create_quickfeedback_options(self) -> None:
        """Create quick feedback options."""
        options = {}
        self.output("Creating quickfeedback options")
        options["na"] = FacilityQuickFeedback.objects.create(
            feedback="N/A",
            icon="fas fa-times",
        )
        options["attention"] = FacilityQuickFeedback.objects.create(
            feedback="Needs attention",
        )
        options["toiletpaper"] = FacilityQuickFeedback.objects.create(
            feedback="Needs more toiletpaper",
            icon="fas fa-toilet-paper",
        )
        options["cleaning"] = FacilityQuickFeedback.objects.create(
            feedback="Needs cleaning",
            icon="fas fa-broom",
        )
        options["power"] = FacilityQuickFeedback.objects.create(
            feedback="No power",
            icon="fas fa-bolt",
        )
        self.quickfeedback_options = options

    def create_mobilepay_transactions(self) -> None:
        """Create MobilePay Transactions."""
        self.output("Creating MobilePay Transactions...")
        MobilePayTransactionFactory.create_batch(50)

    def create_clearhaus_settlements(self) -> None:
        """Create Clearhaus Settlements."""
        self.output("Creating Clearhaus Settlements...")
        ClearhausSettlementFactory.create_batch(50)

    def create_zettle_stuff(self) -> None:
        """Create Zettle receipts and balances."""
        self.output("Creating Zettle receipts and balances...")
        ZettleBalanceFactory.create_batch(100)
        ZettleReceiptFactory.create_batch(100)

    def create_bank_stuff(self) -> None:
        """Create Banks, BankAccounts, and BankTransactions."""
        self.output("Creating Banks, BankAccounts, and BankTransactions...")
        BankFactory.create_batch(2)
        BankAccountFactory.create_batch(16)
        BankTransactionFactory.create_batch(300)

    def create_coinify_stuff(self) -> None:
        """Create coinify invoices, payment intents, payouts, settlements and balances."""
        self.output(
            "Creating Coinify invoices, payment intents, payouts, settlements and balances...",
        )
        CoinifyInvoiceFactory.create_batch(50)
        CoinifyPaymentIntentFactory.create_batch(50)
        CoinifyPayoutFactory.create_batch(10)
        CoinifyBalanceFactory.create_batch(10)
        CoinifySettlementFactory.create_batch(10)

    def create_epay_transactions(self) -> None:
        """Create epay transactions."""
        self.output("Creating ePay Transactions...")
        EpayTransactionFactory.create_batch(50)

    def create_facility_types(self, teams: dict, options: dict) -> dict:
        """Create facility types."""
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

    def create_facilities(self, facility_types: dict) -> dict:
        """Create facilities."""
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

    def create_facility_feedbacks(
        self,
        facilities: dict,
        options: dict,
        users: dict,
    ) -> None:
        """Create facility feedbacks."""
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

    def create_event_types(self) -> None:
        """Create event types."""
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

        types["recreational"] = EventType.objects.create(
            name="Recreational Event",
            slug="recreational-event",
            color="#0000ff",
            light_text=True,
            public=True,
            description="Events of a recreational nature",
            icon="dice",
            host_title="Host",
            event_duration_minutes="600",
            support_autoscheduling=False,
            support_speaker_event_conflicts=True,
        )

        self.event_types = types

    def create_url_types(self) -> None:
        """Create UrlType objects."""
        self.output("Creating UrlType objects...")
        t, created = UrlType.objects.get_or_create(
            name="Other",
            defaults={"icon": "fas fa-link"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Homepage",
            defaults={"icon": "fas fa-link"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Slides",
            defaults={"icon": "fas fa-chalkboard-teacher"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Twitter",
            defaults={"icon": "fab fa-twitter"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Mastodon",
            defaults={"icon": "fab fa-mastodon"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Facebook",
            defaults={"icon": "fab fa-facebook"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Project",
            defaults={"icon": "fas fa-link"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Blog",
            defaults={"icon": "fas fa-link"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Github",
            defaults={"icon": "fab fa-github"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Keybase",
            defaults={"icon": "fab fa-keybase"},
        )
        t, created = UrlType.objects.get_or_create(
            name="Recording",
            defaults={"icon": "fas fa-film"},
        )

    def create_credebtors(self) -> None:
        """Create Chain and Credebtors."""
        self.output("Creating Chains and Credebtors...")
        try:
            CredebtorFactory.create_batch(50)
        except ValidationError:
            self.output("Name conflict, retrying...")
            CredebtorFactory.create_batch(50)
        for _ in range(20):
            # add 20 more credebtors to random existing chains
            try:
                CredebtorFactory.create(chain=Chain.objects.order_by("?").first())
            except ValidationError:
                self.output("Name conflict, skipping...")
                continue
        # add a credebtor for reimbursements
        reimbursement_chain = Chain.objects.create(
            name="Reimbursement",
            notes="This chain is only used for reimbursements",
        )
        Credebtor.objects.create(
            chain=reimbursement_chain,
            name="Reimbursement",
            address="Nowhere",
        )

    def create_product_categories(self) -> None:
        """Create product categories."""
        categories = {}
        self.output("Creating productcategories...")
        categories["transportation"] = ProductCategory.objects.create(
            name="Transportation",
            slug="transportation",
        )
        categories["merchandise"] = ProductCategory.objects.create(
            name="Merchandise",
            slug="merchandise",
        )
        categories["tickets"] = ProductCategory.objects.create(
            name="Tickets",
            slug="tickets",
        )
        categories["villages"] = ProductCategory.objects.create(
            name="Villages",
            slug="villages",
        )
        categories["facilities"] = ProductCategory.objects.create(
            name="Facilities",
            slug="facilities",
        )
        categories["packages"] = ProductCategory.objects.create(
            name="Packages",
            slug="packages",
        )

        self.product_categories = categories

    def create_camp_ticket_types(self, camp: Camp) -> dict:
        """Create camp ticket types."""
        types = {}
        self.output(f"Creating tickettypes for {camp.camp.lower.year}...")
        types["adult_full_week"] = TicketType.objects.create(
            name="Adult Full Week",
            camp=camp,
        )
        camp.ticket_type_full_week_adult = types["adult_full_week"]
        types["adult_one_day"] = TicketType.objects.create(
            name="Adult One Day",
            camp=camp,
        )
        camp.ticket_type_one_day_adult = types["adult_one_day"]
        types["child_full_week"] = TicketType.objects.create(
            name="Child Full Week",
            camp=camp,
        )
        camp.ticket_type_full_week_child = types["child_full_week"]
        types["child_one_day"] = TicketType.objects.create(
            name="Child One Day",
            camp=camp,
        )
        camp.ticket_type_one_day_child = types["child_one_day"]
        types["village"] = TicketType.objects.create(
            name="Village",
            camp=camp,
        )
        types["merchandise"] = TicketType.objects.create(
            name="Merchandise",
            camp=camp,
        )
        types["facilities"] = TicketType.objects.create(
            name="Facilities",
            camp=camp,
            single_ticket_per_product=True,
        )
        types["transportation"] = TicketType.objects.create(
            name="Transportation",
            camp=camp,
        )

        return types

    def create_camp_products(
        self,
        camp: Camp,
        categories: dict,
        ticket_types: dict,
    ) -> dict:
        """Create camp shop products."""
        products = {}
        year = camp.camp.lower.year
        camp_prefix = f"BornHack {year}"

        name = f"{camp_prefix} Standard ticket"
        products["ticket1"] = Product.objects.create(
            name=name,
            description="A ticket",
            price=1200,
            category=categories["tickets"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["tickets"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["adult_full_week"],
        )

        name = f"{camp_prefix} Hacker ticket"
        products["ticket2"] = Product.objects.create(
            name=name,
            description="Another ticket",
            price=1337,
            category=categories["tickets"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["tickets"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["adult_full_week"],
        )

        name = f"{camp_prefix} Child Ticket (5-15 year old)"
        products["child_ticket"] = Product.objects.create(
            name=name,
            description="A child ticket",
            price=495,
            category=categories["tickets"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["tickets"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["child_full_week"],
        )

        name = f"{camp_prefix} One day ticket"
        products["one_day_ticket"] = Product.objects.create(
            name=name,
            description="One day ticket",
            price=300,
            category=categories["tickets"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["tickets"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["adult_one_day"],
        )

        name = f"{camp_prefix} One day ticket child"
        products["one_day_ticket_child"] = Product.objects.create(
            name=name,
            description="One day ticket child",
            price=165,
            category=categories["tickets"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["tickets"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["child_one_day"],
        )

        name = f"{camp_prefix} Village tent 3x3 meters, no floor"
        products["tent1"] = Product.objects.create(
            name=name,
            description="A description of the tent goes here",
            price=3325,
            category=categories["villages"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["villages"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["village"],
        )

        name = f"{camp_prefix} Village tent 3x3 meters, with floor"
        products["tent2"] = Product.objects.create(
            name=name,
            description="A description of the tent goes here",
            price=3675,
            category=categories["villages"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["villages"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["village"],
        )

        name = f"{camp_prefix} T-shirt Large"
        products["t-shirt-large"] = Product.objects.create(
            name=name,
            description="A description of the t-shirt goes here",
            price=150,
            category=categories["merchandise"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["merchandise"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["merchandise"],
        )

        name = f"{camp_prefix} T-shirt Medium"
        products["t-shirt-medium"] = Product.objects.create(
            name=name,
            description="A description of the t-shirt goes here",
            price=150,
            category=categories["merchandise"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["merchandise"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["merchandise"],
        )

        name = f"{camp_prefix} T-shirt Small"
        products["t-shirt-small"] = Product.objects.create(
            name=name,
            description="A description of the t-shirt goes here",
            price=150,
            category=categories["merchandise"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["merchandise"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["merchandise"],
        )

        name = "100 HAX"
        products["hax"] = Product.objects.create(
            name=name,
            description="100 HAX",
            price=100,
            category=categories["facilities"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["facilities"],
                ).values_list("slug", flat=True),
            ),
            ticket_type=ticket_types["facilities"],
        )

        name = "Corporate Hackers Small"
        products["corporate_hackers_small"] = Product.objects.create(
            name=name,
            description="Send your company to BornHack in style with one of our corporate packages!",
            price=18000,
            category=categories["packages"],
            available_in=(
                datetime(year, 1, 1, 12, 0, tzinfo=tz),
                datetime(year, 12, 20, 12, 0, tzinfo=tz),
            ),
            slug=unique_slugify(
                name,
                slugs_in_use=Product.objects.filter(
                    category=categories["packages"],
                ).values_list("slug", flat=True),
            ),
        )
        products["corporate_hackers_small"].sub_products.add(
            products["ticket1"],
            through_defaults={
                "number_of_tickets": 3,
            },
        )
        products["corporate_hackers_small"].sub_products.add(
            products["one_day_ticket"],
            through_defaults={
                "number_of_tickets": 3,
            },
        )
        products["corporate_hackers_small"].sub_products.add(
            products["tent2"],
            through_defaults={
                "number_of_tickets": 1,
            },
        )
        products["corporate_hackers_small"].sub_products.add(
            products["hax"],
            through_defaults={
                "number_of_tickets": 25,
            },
        )

        return products

    def create_orders(self, users: dict, camp_products: dict) -> dict:
        """Create camp orders for products in the shop."""
        orders = {}
        self.output("Creating orders...")
        orders[0] = Order.objects.create(
            user=users[1],
            payment_method="in_person",
            open=None,
            paid=True,
        )
        orders[0].oprs.create(product=camp_products["ticket1"], quantity=1)
        orders[0].oprs.create(product=camp_products["tent1"], quantity=1)
        orders[0].mark_as_paid(request=None)

        orders[1] = Order.objects.create(
            user=users[2],
            payment_method="in_person",
            open=None,
        )
        orders[1].oprs.create(product=camp_products["ticket1"], quantity=1)
        orders[1].oprs.create(product=camp_products["tent2"], quantity=1)
        orders[1].oprs.create(product=camp_products["t-shirt-medium"], quantity=1)
        orders[1].mark_as_paid(request=None)

        orders[2] = Order.objects.create(
            user=users[3],
            payment_method="in_person",
            open=None,
        )
        orders[2].oprs.create(product=camp_products["ticket2"], quantity=1)
        orders[2].oprs.create(product=camp_products["ticket1"], quantity=1)
        orders[2].oprs.create(product=camp_products["tent2"], quantity=1)
        orders[2].oprs.create(product=camp_products["t-shirt-small"], quantity=1)
        orders[2].oprs.create(product=camp_products["t-shirt-large"], quantity=1)
        orders[2].mark_as_paid(request=None)

        orders[3] = Order.objects.create(
            user=users[4],
            payment_method="in_person",
            open=None,
        )
        orders[3].oprs.create(product=camp_products["ticket2"], quantity=1)
        orders[3].oprs.create(product=camp_products["tent1"], quantity=1)
        orders[3].oprs.create(product=camp_products["t-shirt-small"], quantity=1)
        orders[3].oprs.create(product=camp_products["hax"], quantity=30)
        orders[3].mark_as_paid(request=None)

        orders[4] = Order.objects.create(
            user=users[5],
            payment_method="in_person",
            open=None,
        )
        orders[4].oprs.create(product=camp_products["ticket1"], quantity=1)
        orders[4].oprs.create(product=camp_products["child_ticket"], quantity=1)
        orders[4].mark_as_paid(request=None)

        orders[5] = Order.objects.create(
            user=users[6],
            payment_method="in_person",
            open=None,
        )
        orders[5].oprs.create(product=camp_products["one_day_ticket"], quantity=2)
        orders[5].oprs.create(product=camp_products["one_day_ticket_child"], quantity=2)
        orders[5].mark_as_paid(request=None)

        return orders

    def create_camp_tracks(self, camp: Camp) -> dict:
        """Create camp event tracks."""
        tracks = {}
        year = camp.camp.lower.year
        self.output(f"Creating event_tracks for {year}...")
        tracks[1] = EventTrack.objects.create(
            camp=camp,
            name=f"BornHack {year}",
            slug=camp.slug,
        )

        return tracks

    def create_event_locations(self, camp: Camp) -> dict:
        """Create all event locations."""
        locations = {}
        year = camp.camp.lower.year
        self.output(f"Creating event_locations for {year}...")
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
            name="Food Area",
            slug="food-area",
            icon="utensils",
            camp=camp,
            capacity=50,
        )
        locations["infodesk"] = EventLocation.objects.create(
            name="Infodesk",
            slug="infodesk",
            icon="info",
            camp=camp,
            capacity=20,
        )

        # add workshop room conflicts (the big root can not be used while either
        # of the small rooms are in use, and vice versa)
        locations["workshop_room_1"].conflicts.add(locations["workshop_room_2"])
        locations["workshop_room_1"].conflicts.add(locations["workshop_room_3"])

        return locations

    def create_camp_news(self, camp: Camp) -> None:
        """Create camp news."""
        year = camp.camp.lower.year
        self.output(f"Creating news for {year}...")
        NewsItem.objects.create(
            title=f"Welcome to {camp.title}",
            content="news body here with <b>html</b> support",
            published_at=datetime(year, 8, 27, 12, 0, tzinfo=tz),
        )
        NewsItem.objects.create(
            title=f"{camp.title} is over",
            content="news body here",
            published_at=datetime(year, 9, 4, 12, 0, tzinfo=tz),
        )

    def create_camp_event_sessions(
        self,
        camp: Camp,
        event_types: dict,
        event_locations: dict,
    ) -> None:
        """Create camp event sessions."""
        self.output(f"Creating EventSessions for {camp}...")
        days = camp.get_days(camppart="camp")[1:-1]
        for day in days:
            start = day.lower
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["talk"],
                event_location=event_locations["speakers_tent"],
                when=(
                    datetime(start.year, start.month, start.day, 11, 0, tzinfo=tz),
                    datetime(start.year, start.month, start.day, 18, 0, tzinfo=tz),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["recreational"],
                event_location=event_locations["speakers_tent"],
                event_duration_minutes=60,
                when=(
                    datetime(start.year, start.month, start.day, 12, 0, tzinfo=tz),
                    datetime(start.year, start.month, start.day, 13, 0, tzinfo=tz),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["music"],
                event_location=event_locations["bar_area"],
                when=(
                    datetime(start.year, start.month, start.day, 22, 0, tzinfo=tz),
                    datetime(start.year, start.month, start.day, 22, 0, tzinfo=tz) + timedelta(hours=3),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["workshop"],
                event_location=event_locations["workshop_room_1"],
                when=(
                    datetime(start.year, start.month, start.day, 12, 0, tzinfo=tz),
                    datetime(start.year, start.month, start.day, 18, 0, tzinfo=tz),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["workshop"],
                event_location=event_locations["workshop_room_2"],
                when=(
                    datetime(start.year, start.month, start.day, 12, 0, tzinfo=tz),
                    datetime(start.year, start.month, start.day, 18, 0, tzinfo=tz),
                ),
            )
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["workshop"],
                event_location=event_locations["workshop_room_3"],
                when=(
                    datetime(start.year, start.month, start.day, 12, 0, tzinfo=tz),
                    datetime(start.year, start.month, start.day, 18, 0, tzinfo=tz),
                ),
            )
        # create sessions for the keynotes
        for day in [days[1], days[3], days[5]]:
            EventSession.objects.create(
                camp=camp,
                event_type=event_types["keynote"],
                event_location=event_locations["speakers_tent"],
                when=(
                    datetime(
                        day.lower.year,
                        day.lower.month,
                        day.lower.day,
                        20,
                        0,
                        tzinfo=tz,
                    ),
                    datetime(
                        day.lower.year,
                        day.lower.month,
                        day.lower.day,
                        21,
                        30,
                        tzinfo=tz,
                    ),
                ),
            )

    def create_camp_proposals(self, camp: Camp, event_types: dict) -> None:
        """Create camp proposals: talks, workshops and keynotes."""
        year = camp.camp.lower.year
        self.output(f"Creating event- and speaker_proposals for {year}...")

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
            if random.randint(1, 10) > 8:  # noqa: PLR2004, S311
                other_speakers = SpeakerProposal.objects.filter(camp=camp).exclude(
                    uuid=sp.uuid,
                )
                # ... if we have any...
                if other_speakers.exists():
                    # add an extra speaker
                    ep.speakers.add(random.choice(other_speakers))  # noqa: S311

            # add tags for 2 out of 3 events
            if random.choice([True, True, False]):  # noqa: S311
                # add 1-3 tags for this EP
                ep.tags.add(*random.sample(tags, k=random.randint(1, 3)))  # noqa: S311

        EventProposal.objects.create(
            user=random.choice(User.objects.all()),  # noqa: S311
            title="Lunch break",
            abstract="Daily lunch break. Remember to drink water.",
            event_type=event_types["recreational"],
            track=random.choice(camp.event_tracks.all()),  # noqa: S311
        ).mark_as_approved()

    def create_proposal_urls(self, camp: Camp) -> None:
        """Create URL objects for the proposals."""
        year = camp.camp.lower.year
        self.output(
            f"Creating URLs for Speaker- and EventProposals for {year}...",
        )
        SpeakerProposalUrlFactory.create_batch(
            100,
            speaker_proposal=factory.Iterator(
                SpeakerProposal.objects.filter(camp=camp),
            ),
        )
        EventProposalUrlFactory.create_batch(
            100,
            event_proposal=factory.Iterator(
                EventProposal.objects.filter(track__camp=camp),
            ),
        )

    def generate_speaker_availability(self, camp: Camp) -> None:
        """Create SpeakerAvailability objects for the SpeakerProposals."""
        year = camp.camp.lower.year
        self.output(
            f"Generating random SpeakerProposalAvailability for {year}...",
        )
        for sp in camp.speaker_proposals.all():
            # generate a matrix for this speaker_proposals event_types
            matrix = get_speaker_availability_form_matrix(
                sessions=sp.camp.event_sessions.filter(
                    event_type__in=sp.event_types.all(),
                ),
            )

            # build a "form" object so we can reuse save_speaker_availability()
            class FakeForm:
                cleaned_data = {}

            form = FakeForm()
            for daychunks in matrix.values():
                # 90% chance we have info for any given day
                if random.randint(1, 100) > 90:  # noqa: PLR2004, S311
                    # no availability info for this entire day, sorry
                    continue
                for data in daychunks.values():
                    if not data:
                        continue
                    # 90% chance this speaker is available for any given chunk
                    form.cleaned_data[data["fieldname"]] = random.randint(1, 100) < 90
            # print(f"saving availability for speaker {sp}: {form.cleaned_data}")
            save_speaker_availability(form, sp)

    def approve_speaker_proposals(self, camp: Camp) -> None:
        """Approve all keynotes but reject 10% of other events."""
        for sp in camp.speaker_proposals.filter(
            event_proposals__event_type__name="Keynote",
        ):
            sp.mark_as_approved()

        for sp in camp.speaker_proposals.filter(proposal_status="pending"):
            # we do not approve all speakers
            x = random.randint(1, 100)  # noqa: S311
            if x < 90:  # noqa: PLR2004
                sp.mark_as_approved()
            elif x < 95:  # noqa: PLR2004
                # leave this as pending
                continue
            else:
                sp.mark_as_rejected()

    def approve_event_proposals(self, camp: Camp) -> None:
        """Approve event proposals but reject 10% if its not a keynote."""
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
            event.demand = random.randint(10, 40)  # noqa: S311
            event.save()

    def create_camp_scheduling(self, camp: Camp, autoschedule: bool) -> None:
        """Create camp scheduling."""
        year = camp.camp.lower.year
        self.output(f"Creating scheduling for {year}...")

        # create a lunchbreak daily in speakers tent
        lunch = Event.objects.get(track__camp=camp, title="Lunch break")
        for day in camp.get_days(camppart="camp")[1:-1]:
            date = day.lower.date()
            start = datetime(date.year, date.month, date.day, 12, 0, tzinfo=tz)
            lunchslot = EventSlot.objects.get(
                event_session__event_location=camp.event_locations.get(
                    name="Speakers Tent",
                ),
                event_session__event_type=EventType.objects.get(
                    name="Recreational Event",
                ),
                when=(start, start + timedelta(hours=1)),
            )
            lunchslot.event = lunch
            lunchslot.autoscheduled = False
            lunchslot.save()

        # exercise the autoscheduler a bit
        if autoschedule:
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
                f"Done running autoscheduler for {year}... It took {scheduleduration}",
            )

    def create_camp_speaker_event_conflicts(self, camp: Camp) -> None:
        """Create speaker event conflicts."""
        year = camp.camp.lower.year
        self.output(
            f"Generating event_conflicts for SpeakerProposals for {year}...",
        )
        # loop over all
        for sp in camp.speaker_proposals.all():
            # not all speakers add conflicts
            if random.choice([True, True, False]):  # noqa: S311
                # pick 0-10 events this speaker wants to attend
                conflictcount = random.randint(0, 10)  # noqa: S311
                sp.event_conflicts.set(
                    Event.objects.filter(
                        track__camp=camp,
                        event_type__support_speaker_event_conflicts=True,
                    ).order_by("?")[0:conflictcount],
                )

    def create_camp_rescheduling(self, camp: Camp, autoschedule: bool) -> None:
        """Reschedule program for this camp."""
        year = camp.camp.lower.year
        # reapprove all speaker_proposals so the new availability takes effect
        for prop in camp.speaker_proposals.filter(proposal_status="approved"):
            prop.mark_as_approved()
        # exercise the autoscheduler a bit
        self.output(f"Rescheduling {year}...")
        if autoschedule:
            scheduler = AutoScheduler(camp=camp)
            schedulestart = timezone.now()
            try:
                autoschedule, diff = scheduler.calculate_similar_autoschedule()
                scheduler.apply(autoschedule)
            except ValueError as E:
                self.output(
                    f"Got exception while calculating similar autoschedule: {E}",
                )
                autoschedule = None
            scheduleduration = timezone.now() - schedulestart
            self.output(f"Done rescheduling for {year}... It took {scheduleduration}.")

    def create_camp_villages(self, camp: Camp, users: dict) -> None:
        """Create camp villages."""
        year = camp.camp.lower.year
        self.output(f"Creating villages for {year}...")
        Village.objects.create(
            contact=users[1],
            camp=camp,
            name="Baconsvin",
            slug="baconsvin",
            approved=True,
            location=Point(9.9401295, 55.3881695),
            description="The camp with the doorbell-pig! Baconsvin is a group of happy people from Denmark "
            "doing a lot of open source, and are always happy to talk about infosec, hacking, BSD, and much more. "
            "A lot of the organizers of BornHack live in Baconsvin village. "
            "Come by and squeeze the pig and sign our guestbook!",
        )
        Village.objects.create(
            contact=users[2],
            camp=camp,
            name="NetworkWarriors",
            slug="networkwarriors",
            approved=True,
            description="We will have a tent which house the NOC people, various lab equipment people "
            "can play with, and have fun. If you want to talk about networking, come by, and if you have "
            "trouble with the Bornhack network contact us.",
        )
        Village.objects.create(
            contact=users[3],
            camp=camp,
            name="TheCamp.dk",
            slug="the-camp",
            description="This village is representing TheCamp.dk, an annual danish tech camp held in July. "
            "The official subjects for this event is open source software, network and security. "
            "In reality we are interested in anything from computers to illumination soap bubbles and irish coffee",
        )

    def create_camp_teams(self, camp: Camp) -> dict:
        """Create camp teams."""
        teams = {}
        year = camp.camp.lower.year
        self.output(f"Creating teams for {year}...")
        teams["orga"] = Team.objects.create(
            name="Orga",
            description="The Orga team are the main organisers. "
            "All tasks are Orga responsibility until they are delegated to another team",
            camp=camp,
            needs_members=False,
        )
        teams["info"] = Team.objects.create(
            name="Info",
            description="Info team manage the info pages and the info desk.",
            camp=camp,
        )
        teams["poc"] = Team.objects.create(
            name="POC",
            description="The POC team is in charge of establishing and running a phone network onsite.",
            camp=camp,
        )
        teams["noc"] = Team.objects.create(
            name="NOC",
            description="The NOC team is in charge of establishing and running a network onsite.",
            camp=camp,
        )
        teams["game"] = Team.objects.create(
            name="Game",
            description="The Game team is in charge of token game.",
            camp=camp,
        )
        teams["gis"] = Team.objects.create(
            name="GIS",
            description="The GIS team is in charge of managing the gis data.",
            camp=camp,
        )
        teams["bar"] = Team.objects.create(
            name="Bar",
            description="The Bar team plans, builds and run the IRL bar!",
            camp=camp,
        )
        teams["shuttle"] = Team.objects.create(
            name="Shuttle",
            description="The shuttle team drives people to and from the trainstation or the supermarket",
            camp=camp,
        )
        teams["power"] = Team.objects.create(
            name="Power",
            description="The power team makes sure we have power all over the venue",
            camp=camp,
        )
        teams["shit"] = Team.objects.create(
            name="Sanitation",
            description="Team shit takes care of the toilets",
            camp=camp,
        )
        teams["content"] = Team.objects.create(
            name="Content",
            description="The Content Team handles stuff on the program",
            camp=camp,
            mailing_list="content@example.com",
        )
        teams["economy"] = Team.objects.create(
            name="Economy",
            description="The Economy Team handles the money and accounts.",
            camp=camp,
            mailing_list="economy@example.com",
        )
        camp.economy_team = teams["economy"]
        camp.save()
        return teams

    def create_camp_team_tasks(self, camp: Camp, teams: dict) -> None:
        """Create camp team tasks."""
        year = camp.camp.lower.year
        self.output(f"Creating TeamTasks for {year}...")
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
            team=teams["bar"],
            name="Taps",
            description="Taps must be ordered",
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

    def create_camp_team_memberships(
        self,
        camp: Camp,
        teams: dict,
        users: dict,
    ) -> dict:
        """Create camp team memberships."""
        memberships = {}
        year = camp.camp.lower.year
        self.output(f"Creating team memberships for {year}...")
        # noc team
        memberships["noc"] = {}
        memberships["noc"]["user4"] = TeamMember.objects.create(
            team=teams["noc"],
            user=users[4],
            approved=True,
            lead=True,
        )
        memberships["noc"]["user4"].save()
        memberships["noc"]["user1"] = TeamMember.objects.create(
            team=teams["noc"],
            user=users[1],
            approved=True,
        )
        memberships["noc"]["user5"] = TeamMember.objects.create(
            team=teams["noc"],
            user=users[5],
            approved=True,
        )
        memberships["noc"]["user2"] = TeamMember.objects.create(
            team=teams["noc"],
            user=users[2],
        )

        # bar team
        memberships["bar"] = {}
        memberships["bar"]["user1"] = TeamMember.objects.create(
            team=teams["bar"],
            user=users[1],
            approved=True,
            lead=True,
        )
        memberships["bar"]["user3"] = TeamMember.objects.create(
            team=teams["bar"],
            user=users[3],
            approved=True,
            lead=True,
        )
        memberships["bar"]["user2"] = TeamMember.objects.create(
            team=teams["bar"],
            user=users[2],
            approved=True,
        )
        memberships["bar"]["user7"] = TeamMember.objects.create(
            team=teams["bar"],
            user=users[7],
            approved=True,
        )
        memberships["bar"]["user8"] = TeamMember.objects.create(
            team=teams["bar"],
            user=users[8],
        )

        # orga team
        memberships["orga"] = {}
        memberships["orga"]["user8"] = TeamMember.objects.create(
            team=teams["orga"],
            user=users[8],
            approved=True,
            lead=True,
        )
        memberships["orga"]["user9"] = TeamMember.objects.create(
            team=teams["orga"],
            user=users[9],
            approved=True,
            lead=True,
        )
        memberships["orga"]["user4"] = TeamMember.objects.create(
            team=teams["orga"],
            user=users[4],
            approved=True,
            lead=True,
        )

        # shuttle team
        memberships["shuttle"] = {}
        memberships["shuttle"]["user7"] = TeamMember.objects.create(
            team=teams["shuttle"],
            user=users[7],
            approved=True,
            lead=True,
        )
        memberships["shuttle"]["user3"] = TeamMember.objects.create(
            team=teams["shuttle"],
            user=users[3],
            approved=True,
        )
        memberships["shuttle"]["user9"] = TeamMember.objects.create(
            team=teams["shuttle"],
            user=users[9],
        )

        # economy team also gets a member
        TeamMember.objects.create(
            team=teams["economy"],
            user=users[0],
            lead=True,
            approved=True,
        )

        # gis team also gets a member
        TeamMember.objects.create(
            team=teams["gis"],
            user=users[0],
            lead=True,
            approved=True,
        )
        return memberships

    def create_camp_team_shifts(
        self,
        camp: Camp,
        teams: dict,
        team_memberships: dict,
    ) -> None:
        """Create camp team shifts."""
        shifts = {}
        year = camp.camp.lower.year
        self.output(f"Creating team shifts for {year}...")
        shifts[0] = TeamShift.objects.create(
            team=teams["shuttle"],
            shift_range=(
                datetime(year, 8, 27, 2, 0, tzinfo=tz),
                datetime(year, 8, 27, 8, 0, tzinfo=tz),
            ),
            people_required=1,
        )
        shifts[0].team_members.add(team_memberships["shuttle"]["user7"])
        shifts[1] = TeamShift.objects.create(
            team=teams["shuttle"],
            shift_range=(
                datetime(year, 8, 27, 8, 0, tzinfo=tz),
                datetime(year, 8, 27, 14, 0, tzinfo=tz),
            ),
            people_required=1,
        )
        shifts[2] = TeamShift.objects.create(
            team=teams["shuttle"],
            shift_range=(
                datetime(year, 8, 27, 14, 0, tzinfo=tz),
                datetime(year, 8, 27, 20, 0, tzinfo=tz),
            ),
            people_required=1,
        )

    def create_camp_info_categories(self, camp: Camp, teams: dict) -> dict:
        """Create camp info categories."""
        categories = {}
        year = camp.camp.lower.year
        self.output(f"Creating infocategories for {year}...")
        categories["when"] = InfoCategory.objects.create(
            team=teams["orga"],
            headline="When is BornHack happening?",
            anchor="when",
        )
        categories["travel"] = InfoCategory.objects.create(
            team=teams["orga"],
            headline="Travel Information",
            anchor="travel",
        )
        categories["sleep"] = InfoCategory.objects.create(
            team=teams["orga"],
            headline="Where do I sleep?",
            anchor="sleep",
        )
        categories["noc"] = InfoCategory.objects.create(
            team=teams["noc"],
            headline="Where do I plug in?",
            anchor="noc",
        )

        return categories

    def create_camp_info_items(self, camp: Camp, categories: dict) -> None:
        """Create the camp info items."""
        year = camp.camp.lower.year
        self.output(f"Creating infoitems for {year}...")
        InfoItem.objects.create(
            category=categories["when"],
            headline="Opening",
            anchor="opening",
            body=f"BornHack {year} starts saturday, august 27th, at noon (12:00). "
            "It will be possible to access the venue before noon if for example you arrive early "
            "in the morning with the ferry. But please dont expect everything to be ready before noon :)",
        )
        InfoItem.objects.create(
            category=categories["when"],
            headline="Closing",
            anchor="closing",
            body=f"BornHack {year} ends saturday, september 3rd, at noon (12:00). "
            "Rented village tents must be empty and cleaned at this time, ready to take down. "
            "Participants must leave the site no later than 17:00 on the closing day "
            "(or stay and help us clean up).",
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
            body="PROSA, the union of IT-professionals in Denmark, has set up a great deal "
            "for BornHack attendees travelling from Copenhagen to BornHack. For only 125kr, "
            "about 17 euros, you can be transported to the camp on opening day, and back to "
            "Copenhagen at the end of the camp!",
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
            body="BornHack is first and foremost a tent camp. You need to bring a tent to sleep in. "
            "Most people go with some friends and make a camp somewhere at the venue. "
            "See also the section on Villages - you might be able to find some likeminded people to camp with.",
        )
        InfoItem.objects.create(
            category=categories["sleep"],
            headline="Cabins",
            anchor="cabins",
            body="We rent out a few cabins at the venue with 8 beds each for people who don't want to "
            "sleep in tents for some reason. A tent is the cheapest sleeping option (you just need a ticket), "
            "but the cabins are there if you want them.",
        )
        InfoItem.objects.create(
            category=categories["noc"],
            headline="Switches",
            anchor="switches",
            body="We have places for you to get your cable plugged in to a switch",
        )

    def create_camp_feedback(self, camp: Camp, users: dict[User]) -> None:
        """Create camp feedback."""
        year = camp.camp.lower.year
        self.output(f"Creating feedback for {year}...")
        Feedback.objects.create(
            camp=camp,
            user=users[1],
            feedback="Awesome event, will be back next year",
        )
        Feedback.objects.create(
            camp=camp,
            user=users[3],
            feedback="Very nice, though a bit more hot water would be awesome",
        )
        Feedback.objects.create(
            camp=camp,
            user=users[5],
            feedback="Is there a token here?",
        )
        Feedback.objects.create(
            camp=camp,
            user=users[9],
            feedback="That was fun. Thanks!",
        )

    def create_camp_rides(self, camp: Camp, users: dict) -> None:
        """Create camp rides."""
        year = camp.camp.lower.year
        self.output(f"Creating rides for {year}...")
        Ride.objects.create(
            camp=camp,
            user=users[1],
            seats=2,
            from_location="Copenhagen",
            to_location="BornHack",
            when=datetime(year, 8, 27, 12, 0, tzinfo=tz),
            description="I have space for two people and a little bit of luggage",
        )
        Ride.objects.create(
            camp=camp,
            user=users[1],
            seats=2,
            from_location="BornHack",
            to_location="Copenhagen",
            when=datetime(year, 9, 4, 12, 0, tzinfo=tz),
            description="I have space for two people and a little bit of luggage",
        )
        Ride.objects.create(
            camp=camp,
            user=users[4],
            seats=1,
            from_location="Aarhus",
            to_location="BornHack",
            when=datetime(year, 8, 27, 12, 0, tzinfo=tz),
            description="I need a ride and have a large backpack",
        )

    def create_camp_cfp(self, camp: Camp) -> None:
        """Create the camp call for participation."""
        year = camp.camp.lower.year
        self.output(f"Creating CFP for {year}...")
        camp.call_for_participation_open = True
        camp.call_for_participation = f"Please give a talk at Bornhack {year}..."
        camp.save()

    def create_camp_cfs(self, camp: Camp) -> None:
        """Create the camp call for sponsors."""
        year = camp.camp.lower.year
        self.output(f"Creating CFS for {year}...")
        camp.call_for_sponsors_open = True
        camp.call_for_sponsors = f"Please give us ALL the money so that we can make Bornhack {year} the best ever!"
        camp.save()

    def create_camp_sponsor_tiers(self, camp: Camp) -> dict:
        """Create the camp sponsor tiers."""
        tiers = {}
        year = camp.camp.lower.year
        self.output(f"Creating sponsor tiers for {year}...")
        tiers["platinum"] = SponsorTier.objects.create(
            name="Platinum sponsors",
            description="- 10 tickets\n- logo on website\n- physical banner in the speaker's tent\n- "
            "thanks from the podium\n- recruitment area\n- sponsor meeting with organizers\n- "
            "promoted HackMe\n- sponsored social event",
            camp=camp,
            weight=0,
            week_tickets=10,
        )
        tiers["gold"] = SponsorTier.objects.create(
            name="Gold sponsors",
            description="- 10 tickets\n- logo on website\n- physical banner in the speaker's tent\n- "
            "thanks from the podium\n- recruitment area\n- sponsor meeting with organizers\n- promoted HackMe",
            camp=camp,
            weight=1,
            week_tickets=10,
        )
        tiers["silver"] = SponsorTier.objects.create(
            name="Silver sponsors",
            description="- 5 tickets\n- logo on website\n- physical banner in the speaker's tent\n- "
            "thanks from the podium\n- recruitment area\n- sponsor meeting with organizers",
            camp=camp,
            weight=2,
            week_tickets=5,
        )
        tiers["sponsor"] = SponsorTier.objects.create(
            name="Sponsors",
            description="- 2 tickets\n- logo on website\n- physical banner in the speaker's tent\n- "
            "thanks from the podium\n- recruitment area",
            camp=camp,
            weight=3,
            week_tickets=2,
        )

        return tiers

    def create_camp_sponsors(self, camp: Camp, tiers: dict) -> list:
        """Create the camp sponsors."""
        year = camp.camp.lower.year
        sponsors = []
        self.output(f"Creating sponsors for {year}...")
        sponsors.append(
            Sponsor.objects.create(
                name="PROSA",
                tier=tiers["platinum"],
                description="Bus Trip",
                logo_filename="PROSA-logo.png",
                url="https://www.prosa.dk",
            ),
        )
        sponsors.append(
            Sponsor.objects.create(
                name="DKUUG",
                tier=tiers["platinum"],
                description="Speakers tent",
                logo_filename="DKUUGlogo.jpeg",
                url="http://www.dkuug.dk/",
            ),
        )
        sponsors.append(
            Sponsor.objects.create(
                name="LetsGo",
                tier=tiers["silver"],
                description="Shuttle",
                logo_filename="letsgo.png",
                url="https://letsgo.dk",
            ),
        )
        sponsors.append(
            Sponsor.objects.create(
                name="Saxo Bank",
                tier=tiers["gold"],
                description="Cash Sponsorship",
                logo_filename="saxobank.png",
                url="https://home.saxo",
            ),
        )
        sponsors.append(
            Sponsor.objects.create(
                name="CSIS",
                tier=tiers["sponsor"],
                description="Cash Sponsorship",
                logo_filename="CSIS_PRI_LOGO_TURQUOISE_RGB.jpg",
                url="https://csis.dk",
            ),
        )

        return sponsors

    def create_camp_sponsor_tickets(
        self,
        camp: Camp,
        sponsors: list,
        tiers: dict,
        ticket_types: dict,
    ) -> None:
        """Create tickets for camp sponsors"""
        year = camp.camp.lower.year
        self.output(f"Creating sponsor tickets for {year}...")
        for sponsor in sponsors:
            if sponsor.tier == tiers["platinum"] or sponsor.tier == tiers["gold"]:
                for _ in range(10):
                    SponsorTicket.objects.create(
                        sponsor=sponsor,
                        ticket_type=ticket_types["adult_full_week"],
                    )
            elif sponsor.tier == tiers["silver"]:
                for _ in range(5):
                    SponsorTicket.objects.create(
                        sponsor=sponsor,
                        ticket_type=ticket_types["adult_full_week"],
                    )
            elif sponsor.tier == tiers["sponsor"]:
                for _ in range(2):
                    SponsorTicket.objects.create(
                        sponsor=sponsor,
                        ticket_type=ticket_types["adult_full_week"],
                    )

    def create_token_categories(self, camp: Camp) -> dict[str, TokenCategory]:
        """Create the camp tokens."""
        year = camp.camp.lower.year
        self.output(f"Creating token categories for {year}...")
        categories = {}
        categories["physical"], _ = TokenCategory.objects.get_or_create(
            name="Physical",
            description="Tokens exist in the physical space",
        )
        categories["phone"], _ = TokenCategory.objects.get_or_create(
            name="Phone",
            description="Tokens exist in a phoney space",
        )
        categories["electrical"], _ = TokenCategory.objects.get_or_create(
            name="Electrical",
            description="Tokens with power",
        )
        categories["internet"], _ = TokenCategory.objects.get_or_create(
            name="Internet",
            description="Tokens exist in the virtual space",
        )
        categories["website"], _ = TokenCategory.objects.get_or_create(
            name="Website",
            description="Tokens exist on the bornhack website",
        )
        return categories

    def create_camp_tokens(self, camp: Camp, categories: dict) -> dict[Token]:
        """Create the camp tokens."""
        tokens = {}
        year = camp.camp.lower.year
        self.output(f"Creating tokens for {year}...")
        tokens[0] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category=categories["physical"],
            hint="Token in a tent",
            description="Token in the back of the speakers tent (in binary)",
            active=True,
        )
        tokens[1] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category=categories["internet"],
            hint="Social media",
            description="Mastodon",
            active=True,
        )
        tokens[2] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category=categories["website"],
            hint="Web server",
            description="Token hidden in the X-Secret-Token HTTP header on the BornHack website",
            active=True,
        )
        tokens[3] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category=categories["physical"],
            hint="QR Code",
            description="Token in infodesk (QR code)",
            active=True,
        )
        tokens[4] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category=categories["physical"],
            hint="Gadget",
            description=f"Token on the back of the BornHack {year} badge",
            active=True,
        )
        tokens[5] = Token.objects.create(
            camp=camp,
            token=get_random_string(length=32),
            category=categories["website"],
            hint="EXIF",
            description="Token hidden in EXIF data in the logo posted on the website sunday",
            active=True,
        )

        return tokens

    def create_camp_token_finds(
        self,
        camp: Camp,
        tokens: dict[Token],
        users: dict[User],
    ) -> None:
        """Create the camp token finds."""
        year = camp.camp.lower.year
        self.output(f"Creating token finds for {year}...")
        TokenFind.objects.create(token=tokens[3], user=users[4])
        TokenFind.objects.create(token=tokens[5], user=users[4])
        TokenFind.objects.create(token=tokens[2], user=users[7])
        TokenFind.objects.create(token=tokens[1], user=users[3])
        TokenFind.objects.create(token=tokens[4], user=users[2])
        TokenFind.objects.create(token=tokens[5], user=users[6])
        for i in range(6):
            TokenFind.objects.create(token=tokens[i], user=users[1])

    def create_prize_ticket(self, camp: Camp, ticket_types: dict) -> None:
        """Create prize tickets"""
        year = camp.camp.lower.year
        self.output(f"Creating prize tickets for {year}...")
        PrizeTicket.objects.create(
            user=self.users[5],
            comment="Prize winner",
            ticket_type=ticket_types["adult_full_week"],
        )

    def create_camp_expenses(self, camp: Camp) -> None:
        """Create camp expenses."""
        self.output(f"Creating expenses for {camp}...")
        for team in Team.objects.filter(camp=camp):
            ExpenseFactory.create_batch(10, camp=camp, responsible_team=team)

    def create_camp_reimbursements(self, camp: Camp) -> None:
        """Create camp reimbursements."""
        self.output(f"Creating reimbursements for {camp}...")
        users = User.objects.filter(
            id__in=Expense.objects.filter(
                camp=camp,
                reimbursement__isnull=True,
                paid_by_bornhack=False,
                approved=True,
            )
            .values_list("user", flat=True)
            .distinct(),
        )
        for user in users:
            expenses = Expense.objects.filter(
                user=user,
                approved=True,
                reimbursement__isnull=True,
                paid_by_bornhack=False,
            )
            reimbursement = Reimbursement.objects.create(
                camp=camp,
                user=user,
                reimbursement_user=user,
                bank_account=random.randint(1000000000, 100000000000),  # noqa: S311
                notes=f"bootstrap created reimbursement for user {user.username}",
                paid=random.choice([True, True, False]),  # noqa: S311
            )
            expenses.update(reimbursement=reimbursement)
            reimbursement.create_payback_expense()

    def create_camp_revenues(self, camp: Camp) -> None:
        """Method for creating revenue."""
        self.output(f"Creating revenues for {camp}...")
        RevenueFactory.create_batch(20, camp=camp)

    def add_team_permissions(self, camp: Camp) -> None:
        """Assign member permissions to the team groups for this camp."""
        self.output(f"Assigning permissions to team groups for {camp}...")
        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        for team in camp.teams.all():
            permission = Permission.objects.get(
                content_type=permission_content_type,
                codename=f"{team.slug}_team_member",
            )
            team.member_group.permissions.add(permission)

    def create_maps_layer_generic(self) -> None:
        """Create map layers that do not have a camp attached."""
        group = MapGroup.objects.create(name="Generic")
        layer = Layer.objects.create(
            name="Areas",
            slug="areas",
            description="Venue areas",
            icon="fa fa-list-ul",
            group=group,
            public=True,
        )
        Feature.objects.create(
            layer=layer,
            name="Orga",
            description="Orga Area",
            geom=GeometryCollection(
                Polygon(
                    [
                        [9.941073, 55.388305],
                        [9.940768, 55.388103],
                        [9.941146, 55.38796],
                        [9.941149, 55.388035],
                        [9.94132, 55.388201],
                        [9.941073, 55.388305],
                    ],
                ),
            ),
            color="#ff00ffff",
            icon="fa fa-hand-paper",
            url="",
            topic="",
            processing="",
        )

    def create_camp_map_layer(self, camp: Camp) -> None:
        """Create map layers for camp."""
        group = MapGroup.objects.get(name="Generic")
        team = Team.objects.get(name="Orga", camp=camp)
        Layer.objects.create(
            name="Non public layer",
            slug="hiddenlayer",
            description="Hidden layer",
            icon="fa fa-list-ul",
            group=group,
            public=False,
            responsible_team=team,
        )
        layer = Layer.objects.create(
            name="Team Area",
            description="Team areas",
            icon="fa fa-list-ul",
            group=group,
            responsible_team=team,
            public=True,
        )
        Feature.objects.create(
            layer=layer,
            name="Team Area",
            description="Some Team Area",
            geom=GeometryCollection(
                Polygon(
                    [
                        [9.940803, 55.38785],
                        [9.941136, 55.387826],
                        [9.941297, 55.387662],
                        [9.940943, 55.38754],
                        [9.940535, 55.387521],
                        [9.940803, 55.38785],
                    ],
                ),
            ),
            color="#ff00ffff",
            icon="fa fa-list",
            url="",
            topic="",
            processing="",
        )

    def create_camp_pos(self, teams: dict[Team]) -> None:
        """Create POS locations for camp."""
        Pos.objects.create(
            name="Infodesk",
            team=teams["info"],
            external_id="HHR9izotB6HLzgT6k",
        )
        Pos.objects.create(
            name="Bar",
            team=teams["bar"],
            external_id="bTasxE2YYXZh35wtQ",
        )

    def output(self, message: str) -> None:
        """Method for logging the output."""
        logger.info(message)

    def bootstrap_full(self, options: dict) -> None:
        """Bootstrap a full devsite with all the years."""
        camps = [
            {
                "year": 2016,
                "tagline": "Initial Commit",
                "colour": "#004dff",
                "read_only": True,
            },
            {
                "year": 2017,
                "tagline": "Make Tradition",
                "colour": "#750787",
                "read_only": True,
            },
            {
                "year": 2018,
                "tagline": "scale it",
                "colour": "#008026",
                "read_only": True,
            },
            {
                "year": 2019,
                "tagline": "a new /home",
                "colour": "#ffed00",
                "read_only": True,
                "light_text": False,
            },
            {
                "year": 2020,
                "tagline": "Make Clean",
                "colour": "#ff8c00",
                "read_only": True,
            },
            {
                "year": 2021,
                "tagline": "Continuous Delivery",
                "colour": "#e40303",
                "read_only": True,
            },
            {
                "year": 2022,
                "tagline": "black ~/hack",
                "colour": "#000000",
                "read_only": True,
            },
            {
                "year": 2023,
                "tagline": "make legacy",
                "colour": "#613915",
                "read_only": True,
            },
            {
                "year": 2024,
                "tagline": "Feature Creep",
                "colour": "#73d7ee",
                "read_only": False,
                "light_text": False,
            },
            {
                "year": 2025,
                "tagline": "10 Badges",
                "colour": "#ffafc7",
                "read_only": False,
                "light_text": False,
            },
            {
                "year": 2026,
                "tagline": "Undecided",
                "colour": "#ffffff",
                "read_only": False,
                "light_text": False,
            },
        ]
        self.create_camps(camps)
        self.bootstrap_base(options)

    def bootstrap_tests(self) -> None:
        """Method for bootstrapping the test database."""
        camps = [
            {
                "year": 2024,
                "tagline": "Feature Creep",
                "colour": "#73d7ee",
                "read_only": True,
                "light_text": False,
            },
            {
                "year": 2025,
                "tagline": "Undecided",
                "colour": "#ffafc7",
                "read_only": False,
                "light_text": False,
            },
            {
                "year": 2026,
                "tagline": "Undecided",
                "colour": "#ffffff",
                "read_only": False,
                "light_text": False,
            },
        ]
        self.create_camps(camps)
        self.create_users(16)
        self.create_event_types()
        self.create_product_categories()
        teams = {}
        for camp, read_only in self.camps:
            year = camp.camp.lower.year
            if year <= settings.UPCOMING_CAMP_YEAR:
                ticket_types = self.create_camp_ticket_types(camp)
                camp_products = self.create_camp_products(
                    camp,
                    self.product_categories,
                    ticket_types,
                )
                self.create_orders(self.users, camp_products)
                sponsor_tiers = self.create_camp_sponsor_tiers(camp)
                camp_sponsors = self.create_camp_sponsors(camp, sponsor_tiers)
                self.create_camp_sponsor_tickets(
                    camp,
                    camp_sponsors,
                    sponsor_tiers,
                    ticket_types,
                )
                self.create_prize_ticket(camp, ticket_types)

            teams[year] = self.create_camp_teams(camp)
            self.create_camp_team_memberships(camp, teams[year], self.users)
            camp.read_only = read_only
            camp.call_for_participation_open = not read_only
            camp.call_for_sponsors_open = not read_only
            camp.save()

        self.camp = self.camps[1][0]
        self.add_team_permissions(self.camp)
        self.teams = teams[self.camp.camp.lower.year]
        for member in TeamMember.objects.filter(team__camp=self.camp):
            member.save()

    def bootstrap_camp(self, options: dict) -> None:
        """Bootstrap camp related entities."""
        permissions_added = False
        self.teams = {}
        for camp, read_only in self.camps:
            self.output(
                f"----------[ Bornhack {camp.camp.lower.year} ]----------",
            )

            if camp.camp.lower.year <= settings.UPCOMING_CAMP_YEAR:
                ticket_types = self.create_camp_ticket_types(camp)

                camp_products = self.create_camp_products(
                    camp,
                    self.product_categories,
                    ticket_types,
                )

                self.create_orders(self.users, camp_products)

                self.create_camp_tracks(camp)

                locations = self.create_event_locations(camp)

                self.create_camp_news(camp)

                teams = self.create_camp_teams(camp)
                self.teams[camp.camp.lower.year] = teams

                if not read_only and not permissions_added:
                    # add permissions for the first camp that is not read_only
                    self.add_team_permissions(camp)
                    permissions_added = True

                self.create_camp_team_tasks(camp, teams)

                team_memberships = self.create_camp_team_memberships(
                    camp,
                    teams,
                    self.users,
                )

                self.create_camp_team_shifts(camp, teams, team_memberships)

                self.create_camp_pos(teams)

                self.create_camp_cfp(camp)

                self.create_camp_proposals(camp, self.event_types)

                self.create_proposal_urls(camp)

                self.create_camp_event_sessions(camp, self.event_types, locations)

                self.generate_speaker_availability(camp)

                try:
                    self.approve_speaker_proposals(camp)
                except ValidationError:
                    self.output(
                        "Name collision, bad luck. Run the bootstrap script again! "
                        "PRs to make this less annoying welcome :)",
                    )
                    sys.exit(1)

                self.approve_event_proposals(camp)

                self.create_camp_scheduling(camp, not options["skip_auto_scheduler"])

                # shuffle it up - delete and create new random availability
                self.generate_speaker_availability(camp)

                # and create some speaker<>event conflicts
                self.create_camp_speaker_event_conflicts(camp)

                # recalculate the autoschedule
                self.create_camp_rescheduling(camp, not options["skip_auto_scheduler"])

                self.create_camp_villages(camp, self.users)

                facility_types = self.create_facility_types(
                    teams,
                    self.quickfeedback_options,
                )

                facilities = self.create_facilities(facility_types)

                self.create_facility_feedbacks(
                    facilities,
                    self.quickfeedback_options,
                    self.users,
                )

                info_categories = self.create_camp_info_categories(camp, teams)

                self.create_camp_info_items(camp, info_categories)

                self.create_camp_feedback(camp, self.users)

                self.create_camp_rides(camp, self.users)

                self.create_camp_cfs(camp)

                sponsor_tiers = self.create_camp_sponsor_tiers(camp)

                camp_sponsors = self.create_camp_sponsors(camp, sponsor_tiers)

                categories = self.create_token_categories(camp)

                tokens = self.create_camp_tokens(camp, categories)

                self.create_camp_token_finds(camp, tokens, self.users)

                self.create_camp_expenses(camp)

                self.create_camp_reimbursements(camp)

                self.create_camp_revenues(camp)

                self.create_camp_map_layer(camp)
            else:
                self.output("Not creating anything for this year yet")

            camp.read_only = read_only
            camp.call_for_participation_open = not read_only
            camp.call_for_sponsors_open = not read_only
            camp.save()

            # Update team permissions.
            if camp.camp.lower.year == settings.UPCOMING_CAMP_YEAR:
                for member in TeamMember.objects.filter(team__camp=camp):
                    member.save()

    def bootstrap_base(self, options: dict) -> None:
        """Bootstrap the data for the application."""
        self.output(
            "----------[ Running bootstrap_devsite ]----------",
        )

        self.output("----------[ Global stuff ]----------")

        self.create_event_routing_types()
        self.create_users(16)

        self.create_news()

        self.create_event_types()

        self.create_url_types()

        self.create_product_categories()

        self.create_quickfeedback_options()

        self.create_mobilepay_transactions()

        self.create_clearhaus_settlements()

        self.create_credebtors()

        self.create_bank_stuff()

        self.create_coinify_stuff()

        self.create_epay_transactions()

        self.create_maps_layer_generic()

        self.bootstrap_camp(options)

        self.output("----------[ Finishing up ]----------")

        self.output("Adding event routing...")
        teams = self.teams[next(reversed(self.teams.keys()))]
        Routing.objects.create(
            team=teams["orga"],
            eventtype=Type.objects.get(name="public_credit_name_changed"),
        )
        Routing.objects.create(
            team=teams["orga"],
            eventtype=Type.objects.get(name="ticket_created"),
        )

        self.output("done!")
