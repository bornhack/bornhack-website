# coding: utf-8
from django.core.management.base import BaseCommand
from django.utils import timezone
from camps.models import Camp
from news.models import NewsItem
from info.models import InfoCategory, InfoItem
from villages.models import Village
from feedback.models import Feedback
from rideshare.models import Ride
from shop.models import ProductCategory, Product, Order
from program.models import (
    EventType,
    Event,
    EventInstance,
    Speaker,
    EventLocation,
    EventTrack,
)
from tickets.models import TicketType
from teams.models import Team, TeamTask, TeamMember, TeamShift
from events.models import Type, Routing
from profiles.models import Profile
from sponsors.models import SponsorTier, Sponsor
from tokens.models import Token, TokenFind
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.db.models.signals import post_save
import factory
from faker import Faker

fake = Faker()


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


class Command(BaseCommand):
    args = "none"
    help = "Create mock data for development instances"

    def output_fake_md_description(self):
        fake_text = "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
        fake_text += "\n\n"
        fake_text += "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
        fake_text += "\n\n"
        fake_text += "## " + fake.sentence(nb_words=3) + "\n"
        fake_text += "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
        fake_text += "\n\n"
        fake_text += '![The image is not awailable](/static/img/na.jpg "not awailable")'
        fake_text += "\n\n"
        fake_text += "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
        fake_text += "\n\n"
        fake_text += "* [" + fake.sentence(nb_words=3) + "](" + fake.uri() + ")\n"
        fake_text += "* [" + fake.sentence(nb_words=3) + "](" + fake.uri() + ")\n"

        return fake_text

    def output_fake_description(self):
        fake_text = "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
        fake_text += "* [" + fake.sentence(nb_words=3) + "](" + fake.uri() + ")\n"

        return fake_text

    def create_camps(self):
        self.output("Creating camps...")
        camps = [
            dict(year=2016, tagline="Initial Commit", colour="#004dff", read_only=True),
            dict(year=2017, tagline="Make Tradition", colour="#750787", read_only=True),
            dict(year=2018, tagline="scale it", colour="#008026", read_only=True),
            dict(year=2019, tagline="a new /home", colour="#ffed00", read_only=False),
            dict(year=2020, tagline="Undecided", colour="#ff8c00", read_only=False),
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
                            timezone.datetime(year, 8, 25, 12, 0, tzinfo=timezone.utc),
                            timezone.datetime(year, 8, 27, 12, 0, tzinfo=timezone.utc),
                        ),
                        camp=(
                            timezone.datetime(year, 8, 27, 12, 0, tzinfo=timezone.utc),
                            timezone.datetime(year, 9, 4, 11, 0, tzinfo=timezone.utc),
                        ),
                        teardown=(
                            timezone.datetime(year, 9, 4, 12, 0, tzinfo=timezone.utc),
                            timezone.datetime(year, 9, 6, 12, 0, tzinfo=timezone.utc),
                        ),
                        colour=camp["colour"],
                    ),
                    read_only,
                )
            )

        return camp_instances

    def create_users(self):
        self.output("Creating users...")

        users = {}

        for i in range(1, 10):
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
        )

        types["keynote"] = EventType.objects.create(
            name="Keynote",
            slug="keynote",
            color="#FF3453",
            light_text=True,
            description="A keynote presentation",
            icon="star",
            host_title="Speaker",
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
        )

        types["slack"] = EventType.objects.create(
            name="Recreational Event",
            slug="recreational-event",
            color="#0000ff",
            light_text=True,
            public=True,
            description="Events of a recreational nature",
            icon="dice",
            host_title="Host",
        )

        return types

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
                timezone.datetime(2017, 3, 1, 11, 0, tzinfo=timezone.utc),
                timezone.datetime(2017, 10, 30, 11, 30, tzinfo=timezone.utc),
            ),
            slug="{}".format(slugify(name)),
        )

        name = "PROSA bus transport (open for everyone)"
        products["product1"] = Product.objects.create(
            name=name,
            category=categories["transportation"],
            price=125,
            description="PROSA is sponsoring a bustrip from Copenhagen to the venue and back.",
            available_in=(
                timezone.datetime(2017, 3, 1, 11, 0, tzinfo=timezone.utc),
                timezone.datetime(2017, 10, 30, 11, 30, tzinfo=timezone.utc),
            ),
            slug="{}".format(slugify(name)),
        )

        name = "T-shirt (large)"
        products["product2"] = Product.objects.create(
            name=name,
            category=categories["merchandise"],
            price=160,
            description="Get a nice t-shirt",
            available_in=(
                timezone.datetime(2017, 3, 1, 11, 0, tzinfo=timezone.utc),
                timezone.datetime(2017, 10, 30, 11, 30, tzinfo=timezone.utc),
            ),
            slug="{}".format(slugify(name)),
        )

        name = "Village tent 3x3 meters, no floor"
        products["tent1"] = Product.objects.create(
            name=name,
            description="A description of the tent goes here",
            price=3325,
            category=categories["villages"],
            available_in=(
                timezone.datetime(2017, 3, 1, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2017, 8, 20, 12, 0, tzinfo=timezone.utc),
            ),
            slug="{}".format(slugify(name)),
        )

        name = "Village tent 3x3 meters, with floor"
        products["tent2"] = Product.objects.create(
            name=name,
            description="A description of the tent goes here",
            price=3675,
            category=categories["villages"],
            available_in=(
                timezone.datetime(2017, 3, 1, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2017, 8, 20, 12, 0, tzinfo=timezone.utc),
            ),
            slug="{}".format(slugify(name)),
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
                timezone.datetime(year, 1, 1, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 12, 20, 12, 0, tzinfo=timezone.utc),
            ),
            slug="{}".format(slugify(name)),
            ticket_type=ticket_types["adult_full_week"],
        )

        name = "BornHack {} Hacker ticket".format(year)
        products["ticket2"] = Product.objects.create(
            name=name,
            description="Another ticket",
            price=1337,
            category=categories["tickets"],
            available_in=(
                timezone.datetime(year, 1, 1, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 12, 20, 12, 0, tzinfo=timezone.utc),
            ),
            slug="{}".format(slugify(name)),
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
        self.output("Creating eventtracks for {}...".format(year))
        tracks[1] = EventTrack.objects.create(
            camp=camp, name="BornHack", slug=camp.slug
        )

        return tracks

    def create_camp_locations(self, camp):
        locations = {}
        year = camp.camp.lower.year
        self.output("Creating eventlocations for {}...".format(year))
        locations["speakers_tent"] = EventLocation.objects.create(
            name="Speakers Tent", slug="speakers-tent", icon="comment", camp=camp
        )
        locations["workshop_room"] = EventLocation.objects.create(
            name="Workshop rooms", slug="workshop-rooms", icon="briefcase", camp=camp
        )
        locations["bar_area"] = EventLocation.objects.create(
            name="Bar Area", slug="bar-area", icon="glass", camp=camp
        )
        locations["food_area"] = EventLocation.objects.create(
            name="Food Area", slug="food-area", icon="cutlery", camp=camp
        )

        return locations

    def create_camp_news(self, camp):
        year = camp.camp.lower.year
        self.output("Creating news for {}...".format(year))
        NewsItem.objects.create(
            title="Welcome to {}".format(camp.title),
            content="news body here with <b>html</b> support",
            published_at=timezone.datetime(year, 8, 27, 12, 0, tzinfo=timezone.utc),
        )
        NewsItem.objects.create(
            title="{} is over".format(camp.title),
            content="news body here",
            published_at=timezone.datetime(year, 9, 4, 12, 0, tzinfo=timezone.utc),
        )

    def create_camp_events(self, camp, tracks, event_types):
        events = {}
        year = camp.camp.lower.year
        self.output("Creating events for {}...".format(year))
        events[1] = Event.objects.create(
            title="Developing the BornHack website",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[2] = Event.objects.create(
            title="State of the world",
            abstract=self.output_fake_md_description(),
            event_type=event_types["keynote"],
            track=tracks[1],
        )
        events[3] = Event.objects.create(
            title="Welcome to bornhack!",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[4] = Event.objects.create(
            title="bar is open",
            abstract=self.output_fake_md_description(),
            event_type=event_types["facility"],
            track=tracks[1],
        )
        events[5] = Event.objects.create(
            title="Network something",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[6] = Event.objects.create(
            title="State of outer space",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[9] = Event.objects.create(
            title="The Alternative Welcoming",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[10] = Event.objects.create(
            title="Words and Power - are we making the most of online activism?",
            abstract=self.output_fake_md_description(),
            event_type=event_types["keynote"],
            track=tracks[1],
        )
        events[11] = Event.objects.create(
            title="r4d1o hacking 101",
            abstract=self.output_fake_md_description(),
            event_type=event_types["workshop"],
            track=tracks[1],
        )
        events[12] = Event.objects.create(
            title="Introduction to Sustainable Growth in a Digital World",
            abstract=self.output_fake_md_description(),
            event_type=event_types["workshop"],
            track=tracks[1],
        )
        events[13] = Event.objects.create(
            title="American Fuzzy Lop and Address Sanitizer",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[14] = Event.objects.create(
            title="PGP Keysigning Party",
            abstract=self.output_fake_md_description(),
            event_type=event_types["workshop"],
            track=tracks[1],
        )
        events[15] = Event.objects.create(
            title="Bluetooth Low Energy",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[16] = Event.objects.create(
            title="TLS attacks and the burden of faulty TLS implementations",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[17] = Event.objects.create(
            title="State of the Network",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[18] = Event.objects.create(
            title="Running Exit Nodes in the North",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[19] = Event.objects.create(
            title="Hacker Jeopardy Qualifier",
            abstract=self.output_fake_description(),
            event_type=event_types["slack"],
            track=tracks[1],
        )
        events[20] = Event.objects.create(
            title="Hacker Jeopardy Finals",
            abstract=self.output_fake_description(),
            event_type=event_types["slack"],
            track=tracks[1],
        )
        events[21] = Event.objects.create(
            title="Incompleteness Phenomena in Mathematics: From Kurt Gödel to Harvey Friedman",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[22] = Event.objects.create(
            title="Infocalypse Now - and how to Survive It?",
            abstract=self.output_fake_md_description(),
            event_type=event_types["keynote"],
            track=tracks[1],
        )
        events[23] = Event.objects.create(
            title="Liquid Democracy (Introduction and Debate)",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[24] = Event.objects.create(
            title="Badge Workshop",
            abstract=self.output_fake_md_description(),
            event_type=event_types["workshop"],
            track=tracks[1],
        )
        events[25] = Event.objects.create(
            title="Checking a Distributed Hash Table for Correctness",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[26] = Event.objects.create(
            title="GraphQL - A Data Language",
            abstract=self.output_fake_md_description(),
            event_type=event_types["talk"],
            track=tracks[1],
        )
        events[27] = Event.objects.create(
            title="Visualisation of Public Datasets",
            abstract=self.output_fake_md_description(),
            event_type=event_types["workshop"],
            track=tracks[1],
        )
        events[28] = Event.objects.create(
            title="Local delicacies",
            abstract=self.output_fake_md_description(),
            event_type=event_types["facility"],
            track=tracks[1],
        )
        events[29] = Event.objects.create(
            title="Local delicacies from the world",
            abstract=self.output_fake_md_description(),
            event_type=event_types["facility"],
            track=tracks[1],
        )

        return events

    def create_camp_speakers(self, camp, events):
        speakers = {}
        year = camp.camp.lower.year
        self.output("Creating speakers for {}...".format(year))
        speakers[1] = Speaker.objects.create(
            name="Henrik Kramse",
            biography=self.output_fake_description(),
            slug="henrik-kramshj",
            camp=camp,
            email="email@example.com",
        )
        speakers[1].events.add(events[5])
        speakers[2] = Speaker.objects.create(
            name="Thomas Tykling",
            biography=self.output_fake_description(),
            slug="thomas-tykling",
            camp=camp,
            email="email@example.com",
        )
        speakers[2].events.add(events[3], events[1])
        speakers[3] = Speaker.objects.create(
            name="Alex Ahf",
            biography=self.output_fake_description(),
            slug="alex-ahf",
            camp=camp,
            email="email@example.com",
        )
        speakers[3].events.add(events[4], events[2])
        speakers[4] = Speaker.objects.create(
            name="Jesper Arp",
            biography=self.output_fake_description(),
            slug="jesper-arp",
            camp=camp,
            email="email@example.com",
        )
        speakers[4].events.add(events[9], events[27])
        speakers[5] = Speaker.objects.create(
            name="Rolf Bjerre",
            biography=self.output_fake_description(),
            slug="rolf-bjerre",
            camp=camp,
            email="email@example.com",
        )
        speakers[5].events.add(events[9], events[23])
        speakers[6] = Speaker.objects.create(
            name="Emma Holten",
            biography=self.output_fake_description(),
            slug="emma-holten",
            camp=camp,
            email="email@example.com",
        )
        speakers[6].events.add(events[10])
        speakers[7] = Speaker.objects.create(
            name="Christoffer Jerkeby",
            biography=self.output_fake_description(),
            slug="christoffer-jerkeby",
            camp=camp,
            email="email@example.com",
        )
        speakers[7].events.add(events[11])
        speakers[8] = Speaker.objects.create(
            name="Stephan Engberg",
            biography=self.output_fake_description(),
            slug="stephan-engberg",
            camp=camp,
            email="email@example.com",
        )
        speakers[8].events.add(events[12])
        speakers[9] = Speaker.objects.create(
            name="Hanno Böck",
            biography=self.output_fake_description(),
            slug="hanno-bock",
            camp=camp,
            email="email@example.com",
        )
        speakers[9].events.add(events[13], events[16])
        speakers[10] = Speaker.objects.create(
            name="Ximin Luo",
            biography=self.output_fake_description(),
            slug="ximin-luo",
            camp=camp,
            email="email@example.com",
        )
        speakers[10].events.add(events[14])
        speakers[11] = Speaker.objects.create(
            name="Michael Knudsen",
            biography=self.output_fake_description(),
            slug="michael-knudsen",
            camp=camp,
            email="email@example.com",
        )
        speakers[11].events.add(events[15])
        speakers[12] = Speaker.objects.create(
            name="BornHack Network Team",
            biography=self.output_fake_description(),
            slug="bornhack-network-team",
            camp=camp,
            email="email@example.com",
        )
        speakers[12].events.add(events[17])
        speakers[13] = Speaker.objects.create(
            name="Juha Nurmi",
            biography=self.output_fake_description(),
            slug="juha-nurmi",
            camp=camp,
            email="email@example.com",
        )
        speakers[13].events.add(events[18])
        speakers[14] = Speaker.objects.create(
            name="Lasse Andersen",
            biography=self.output_fake_description(),
            slug="lasse-andersen",
            camp=camp,
            email="email@example.com",
        )
        speakers[14].events.add(events[21])
        speakers[15] = Speaker.objects.create(
            name="Anders Kjærulff",
            biography=self.output_fake_description(),
            slug="anders-kjrulff",
            camp=camp,
            email="email@example.com",
        )
        speakers[15].events.add(events[22])
        speakers[16] = Speaker.objects.create(
            name="Thomas Flummer",
            biography=self.output_fake_description(),
            slug="thomas-flummer",
            camp=camp,
            email="email@example.com",
        )
        speakers[16].events.add(events[24])
        speakers[17] = Speaker.objects.create(
            name="Jesper Louis Andersen",
            biography=self.output_fake_description(),
            slug="jesper-louis-andersen",
            camp=camp,
            email="email@example.com",
        )
        speakers[17].events.add(events[25], events[26])

        return speakers

    def create_camp_scheduling(self, camp, events, locations):
        year = camp.camp.lower.year
        self.output("Creating eventinstances for {}...".format(year))
        EventInstance.objects.create(
            event=events[3],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 27, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 27, 13, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[1],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 28, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 28, 13, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[2],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 29, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 29, 13, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[4],
            location=locations["bar_area"],
            when=(
                timezone.datetime(year, 8, 27, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 28, 5, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[4],
            location=locations["bar_area"],
            when=(
                timezone.datetime(year, 8, 28, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 29, 5, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[4],
            location=locations["bar_area"],
            when=(
                timezone.datetime(year, 8, 29, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 30, 5, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[4],
            location=locations["bar_area"],
            when=(
                timezone.datetime(year, 8, 30, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 31, 5, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[4],
            location=locations["bar_area"],
            when=(
                timezone.datetime(year, 8, 31, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 1, 5, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[4],
            location=locations["bar_area"],
            when=(
                timezone.datetime(year, 9, 1, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 2, 5, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[4],
            location=locations["bar_area"],
            when=(
                timezone.datetime(year, 9, 2, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 3, 5, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[5],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 28, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 28, 13, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[6],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 29, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 29, 13, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[9],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 30, 11, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 30, 11, 30, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[10],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 30, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 30, 13, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[12],
            location=locations["workshop_room"],
            when=(
                timezone.datetime(year, 8, 30, 9, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 30, 11, 30, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[11],
            location=locations["workshop_room"],
            when=(
                timezone.datetime(year, 8, 31, 14, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 31, 16, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[18],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 9, 2, 14, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 2, 15, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[18],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 9, 2, 16, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 2, 17, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[15],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 9, 1, 15, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 1, 16, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[14],
            location=locations["workshop_room"],
            when=(
                timezone.datetime(year, 8, 31, 21, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 31, 22, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[16],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 9, 1, 14, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 1, 15, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[13],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 31, 17, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 31, 18, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[19],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 30, 22, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 30, 23, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[19],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 29, 22, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 29, 23, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[19],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 28, 22, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 28, 23, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[19],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 31, 22, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 31, 23, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[19],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 9, 1, 22, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 1, 23, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[20],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 9, 2, 20, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 2, 22, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[21],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 28, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 28, 13, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[22],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 28, 18, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 28, 19, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[23],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 29, 9, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 29, 11, 30, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[24],
            location=locations["workshop_room"],
            when=(
                timezone.datetime(year, 8, 29, 20, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 29, 22, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[25],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 9, 1, 17, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 1, 18, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[26],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 8, 30, 11, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 30, 12, 0, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[26],
            location=locations["speakers_tent"],
            when=(
                timezone.datetime(year, 9, 1, 11, 45, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 1, 12, 30, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[28],
            location=locations["food_area"],
            when=(
                timezone.datetime(year, 9, 1, 18, 30, tzinfo=timezone.utc),
                timezone.datetime(year, 9, 1, 21, 30, tzinfo=timezone.utc),
            ),
        )
        EventInstance.objects.create(
            event=events[29],
            location=locations["food_area"],
            when=(
                timezone.datetime(year, 8, 29, 18, 30, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 29, 23, 30, tzinfo=timezone.utc),
            ),
        )

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
        )
        teams["noc"] = Team.objects.create(
            name="NOC",
            description="The NOC team is in charge of establishing and running a network onsite.",
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
                timezone.datetime(year, 8, 27, 2, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 27, 8, 0, tzinfo=timezone.utc),
            ),
            people_required=1,
        )
        shifts[0].team_members.add(team_memberships["shuttle"]["user7"])
        shifts[1] = TeamShift.objects.create(
            team=teams["shuttle"],
            shift_range=(
                timezone.datetime(year, 8, 27, 8, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 27, 14, 0, tzinfo=timezone.utc),
            ),
            people_required=1,
        )
        shifts[2] = TeamShift.objects.create(
            team=teams["shuttle"],
            shift_range=(
                timezone.datetime(year, 8, 27, 14, 0, tzinfo=timezone.utc),
                timezone.datetime(year, 8, 27, 20, 0, tzinfo=timezone.utc),
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
            body=self.output_fake_md_description(),
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
            body=self.output_fake_md_description(),
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
            when=timezone.datetime(year, 8, 27, 12, 0, tzinfo=timezone.utc),
            description="I have space for two people and a little bit of luggage",
        )
        Ride.objects.create(
            camp=camp,
            user=users[1],
            seats=2,
            from_location="BornHack",
            to_location="Copenhagen",
            when=timezone.datetime(year, 9, 4, 12, 0, tzinfo=timezone.utc),
            description="I have space for two people and a little bit of luggage",
        )
        Ride.objects.create(
            camp=camp,
            user=users[4],
            seats=1,
            from_location="Aarhus",
            to_location="BornHack",
            when=timezone.datetime(year, 8, 27, 12, 0, tzinfo=timezone.utc),
            description="I need a ride and have a large backpack",
        )

    def create_camp_cfp(self, camp):
        year = camp.camp.lower.year
        self.output("Creating CFP for {}...".format(year))
        camp.call_for_participation_open = True
        camp.call_for_participation = "Please give a talk at Bornhack {}...".format(
            year
        )

    def create_camp_cfs(self, camp):
        year = camp.camp.lower.year
        self.output("Creating CFS for {}...".format(year))
        camp.call_for_sponsors_open = True
        camp.call_for_sponsors = "Please give us ALL the money so that we can make Bornhack {} the best ever!".format(
            year
        )

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
        self.output("----------[ Global stuff ]----------")

        camps = self.create_camps()
        users = self.create_users()

        self.create_news()

        event_types = self.create_event_types()

        product_categories = self.create_product_categories()

        global_products = self.create_global_products(product_categories)

        for (camp, read_only) in camps:
            year = camp.camp.lower.year

            self.output(
                self.style.SUCCESS("----------[ Bornhack {} ]----------".format(year))
            )

            if year < 2020:
                ticket_types = self.create_camp_ticket_types(camp)

                camp_products = self.create_camp_products(
                    camp, product_categories, ticket_types
                )

                orders = self.create_orders(users, global_products, camp_products)

                tracks = self.create_camp_tracks(camp)

                locations = self.create_camp_locations(camp)

                self.create_camp_news(camp)

                events = self.create_camp_events(camp, tracks, event_types)

                speakers = self.create_camp_speakers(camp, events)

                self.create_camp_scheduling(camp, events, locations)

                self.create_camp_villages(camp, users)

                teams = self.create_camp_teams(camp)

                self.create_camp_team_tasks(camp, teams)

                team_memberships = self.create_camp_team_memberships(camp, teams, users)

                self.create_camp_team_shifts(camp, teams, team_memberships)

                info_categories = self.create_camp_info_categories(camp, teams)

                self.create_camp_info_items(camp, info_categories)

                self.create_camp_feedback(camp, users)

                self.create_camp_rides(camp, users)

                self.create_camp_cfp(camp)

                self.create_camp_cfs(camp)

                sponsor_tiers = self.create_camp_sponsor_tiers(camp)

                self.create_camp_sponsors(camp, sponsor_tiers)

                tokens = self.create_camp_tokens(camp)

                self.create_camp_token_finds(camp, tokens, users)
            else:
                self.output("Not creating anything for this year yet")

            camp.read_only = read_only
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
