from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from camps.models import Camp
from news.models import NewsItem
from program.models import EventType, Event, EventInstance, Speaker
import datetime
from django.contrib.auth.models import User 


class Command(BaseCommand):
    args = 'none'
    help = 'Create mock data for development instances'

    def output(self, message):
        self.stdout.write('%s: %s' % (timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message))

    def handle(self, *args, **options):
        self.output('Creating camps...')
        camp1 = Camp.objects.create(
            title='BornHack 2016',
            tagline='Initial Commit',
            slug='bornhack-2016',
            buildup = (
                timezone.datetime(2016, 8, 25, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 27, 12, 0, tzinfo=timezone.utc),
            ),
            camp = (
                timezone.datetime(2016, 8, 27, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 9, 04, 12, 0, tzinfo=timezone.utc),
            ),
            teardown = (
                timezone.datetime(2016, 9, 04, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 9, 06, 12, 0, tzinfo=timezone.utc),
            ),
        )

        camp2 = Camp.objects.create(
            title='BornHack 2017',
            tagline='Make Tradition',
            slug='bornhack-2017',
            buildup = (
                timezone.datetime(2017, 8, 20, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2017, 8, 22, 12, 0, tzinfo=timezone.utc),
            ),
            camp = (
                timezone.datetime(2017, 8, 22, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2017, 8, 29, 12, 0, tzinfo=timezone.utc),
            ),
            teardown = (
                timezone.datetime(2015, 8, 29, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2015, 8, 31, 12, 0, tzinfo=timezone.utc),
            ),
        )

        camp3 = Camp.objects.create(
            title='BornHack 2018',
            tagline='Undecided',
            slug='bornhack-2018',
            buildup = (
                timezone.datetime(2018, 8, 13, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2018, 8, 16, 12, 0, tzinfo=timezone.utc),
            ),
            camp = (
                timezone.datetime(2018, 8, 16, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2018, 8, 23, 12, 0, tzinfo=timezone.utc),
            ),
            teardown = (
                timezone.datetime(2018, 8, 23, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2018, 8, 26, 12, 0, tzinfo=timezone.utc),
            ),
        )

        self.output('Creating news...')
        news1 = NewsItem.objects.create(
            title='welcome to bornhack 2016',
            content='news body here with <b>html</b> support',
            published_at=timezone.datetime(2016, 8, 27, 12, 0, tzinfo=timezone.utc)
        )
        news2 = NewsItem.objects.create(
            title='bornhack 2016 is over',
            content='news body here',
            published_at=timezone.datetime(2016, 9, 4, 12, 0, tzinfo=timezone.utc)
        )
        news3 = NewsItem.objects.create(
            title='unpublished news item',
            content='unpublished news body here',
        )
        news4 = NewsItem.objects.create(
            title='welcome to bornhack 2017',
            content='news body here',
            published_at=timezone.datetime(2017, 8, 22, 12, 0, tzinfo=timezone.utc),
            archived=True
        )
        news5 = NewsItem.objects.create(
            title='bornhack 2017 is over',
            content='news body here',
            published_at=timezone.datetime(2017, 8, 29, 12, 0, tzinfo=timezone.utc),
            archived=True
        )

        self.output("creating users...")
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='user1',
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='user2',
        )
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='user3',
        )
        user4 = User.objects.create_user(
            username='user4',
            email='user4@example.com',
            password='user4',
        )
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin',
        )

        self.output("creating event types...")
        et1 = EventType.objects.create(
            name='Workshops',
            slug='workshops',
            color='#ff9900',
            light_text=False
        )

        et2 = EventType.objects.create(
            name='Talks',
            slug='talks',
            color='#2D9595',
            light_text=True
        )

        et3 = EventType.objects.create(
            name='Keynotes',
            slug='keynotes',
            color='#FF3453',
            light_text=True
        )

        et4 = EventType.objects.create(
            name='Facilities',
            slug='facilities',
            color='#cccccc',
            light_text=False
        )


        self.output("creating events...")
        ev1 = Event.objects.create(
            title='Developing the BornHack website',
            abstract='abstract here, bla bla bla',
            event_type=et2,
            camp=camp1
        )
        ev2 = Event.objects.create(
            title='State of the world',
            abstract='abstract here, bla bla bla',
            event_type=et3,
            camp=camp1
        )
        ev3 = Event.objects.create(
            title='Welcome to bornhack!',
            abstract='abstract here, bla bla bla',
            event_type=et2,
            camp=camp1
        )
        ev4 = Event.objects.create(
            title='bar is open',
            abstract='the bar is open, yay',
            event_type=et4,
            camp=camp1
        )

        ev5 = Event.objects.create(
            title='Network something',
            abstract='abstract here, bla bla bla',
            event_type=et2,
            camp=camp2
        )
        ev6 = Event.objects.create(
            title='State of outer space',
            abstract='abstract here, bla bla bla',
            event_type=et3,
            camp=camp2
        )
        ev7 = Event.objects.create(
            title='Welcome to bornhack!',
            abstract='abstract here, bla bla bla',
            event_type=et2,
            camp=camp2
        )
        ev8 = Event.objects.create(
            title='bar is open',
            abstract='the bar is open, yay',
            event_type=et4,
            camp=camp2
        )


        self.output("creating speakers...")
        sp1 = Speaker.objects.create(
            name='Henrik Kramse',
            biography='Henrik is an internet samurai working in internet and security around the world.',
            slug='henrik-kramshj'
        )
        sp1.events.add(ev5, ev6)
        sp2 = Speaker.objects.create(
            name='Thomas Tykling',
            biography='random danish hacker',
            slug='thomas-tykling'
        )
        sp2.events.add(ev7, ev3, ev1)
        sp3 = Speaker.objects.create(
            name='Alex Ahf',
            biography='functional alcoholic',
            slug='alex-ahf'
        )
        sp3.events.add(ev4, ev8, ev2)
 
        self.output("creating eventinstances...")
        ei1 = EventInstance.objects.create(
            event=ev3,
            when=(
                timezone.datetime(2016, 8, 27, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 27, 13, 0, tzinfo=timezone.utc)
            )
        )
        ei2 = EventInstance.objects.create(
            event=ev1,
            when=(
                timezone.datetime(2016, 8, 28, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 28, 13, 0, tzinfo=timezone.utc),
            )
        )
        ei3 = EventInstance.objects.create(
            event=ev2,
            when=(
                timezone.datetime(2016, 8, 29, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 29, 13, 0, tzinfo=timezone.utc),
            )
        )
        ei4 = EventInstance.objects.create(
            event=ev4,
            when=(
                timezone.datetime(2016, 8, 27, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 28, 5, 0, tzinfo=timezone.utc),
            )
        )
        ei5 = EventInstance.objects.create(
            event=ev4,
            when=(
                timezone.datetime(2016, 8, 28, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 29, 5, 0, tzinfo=timezone.utc),
            )
        )
        ei6 = EventInstance.objects.create(
            event=ev4,
            when=(
                timezone.datetime(2016, 8, 29, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 30, 5, 0, tzinfo=timezone.utc),
            )
        )
        ei7 = EventInstance.objects.create(
            event=ev4,
            when=(
                timezone.datetime(2016, 8, 30, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 31, 5, 0, tzinfo=timezone.utc),
            )
        )

        ei8 = EventInstance.objects.create(
            event=ev7,
            when=(
                timezone.datetime(2016, 8, 27, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 27, 13, 0, tzinfo=timezone.utc),
            )
        )
        ei9 = EventInstance.objects.create(
            event=ev5,
            when=(
                timezone.datetime(2016, 8, 28, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 28, 13, 0, tzinfo=timezone.utc),
            )
        )
        ei10 = EventInstance.objects.create(
            event=ev6,
            when=(
                timezone.datetime(2016, 8, 29, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 29, 13, 0, tzinfo=timezone.utc),
            )
        )
        ei11 = EventInstance.objects.create(
            event=ev8,
            when=(
                timezone.datetime(2016, 8, 27, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 28, 5, 0, tzinfo=timezone.utc),
            )
        )
        ei12 = EventInstance.objects.create(
            event=ev8,
            when=(
                timezone.datetime(2016, 8, 28, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 29, 5, 0, tzinfo=timezone.utc),
            )
        )
        ei13 = EventInstance.objects.create(
            event=ev8,
            when=(
                timezone.datetime(2016, 8, 29, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 30, 5, 0, tzinfo=timezone.utc),
            )
        )
        ei14 = EventInstance.objects.create(
            event=ev8,
            when=(
                timezone.datetime(2016, 8, 30, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 31, 5, 0, tzinfo=timezone.utc),
            )
        )


        self.output("created users user1/user1 user2/user2 user3/user3 user4/user4 and admin user admin/admin")
        self.output("done!")

