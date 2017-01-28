# coding: utf-8
from django.core.management.base import BaseCommand
from django.utils import timezone
from camps.models import Camp
from news.models import NewsItem
from shop.models import ProductCategory, Product
from info.models import InfoCategory, InfoItem
from villages.models import Village
from program.models import EventType, Event, EventInstance, Speaker
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
                timezone.datetime(2016, 8, 27, 11, 59, tzinfo=timezone.utc),
            ),
            camp = (
                timezone.datetime(2016, 8, 27, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 9, 04, 11, 59, tzinfo=timezone.utc),
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
                timezone.datetime(2017, 8, 29, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2017, 8, 31, 12, 0, tzinfo=timezone.utc),
            ),
        )

        camp3 = Camp.objects.create(
            title='BornHack 2018',
            tagline='Undecided',
            slug='bornhack-2018',
            buildup = (
                timezone.datetime(2018, 8, 13, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2018, 8, 16, 12, 00, tzinfo=timezone.utc),
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
        workshop = EventType.objects.create(
            name='Workshops',
            slug='workshops',
            color='#ff9900',
            light_text=False
        )

        talk = EventType.objects.create(
            name='Talks',
            slug='talks',
            color='#2D9595',
            light_text=True
        )

        keynote = EventType.objects.create(
            name='Keynotes',
            slug='keynotes',
            color='#FF3453',
            light_text=True
        )

        facility = EventType.objects.create(
            name='Facilities',
            slug='facilities',
            color='#cccccc',
            light_text=False
        )

        self.output("creating events...")
        ev1 = Event.objects.create(
            title='Developing the BornHack website',
            abstract='abstract here, bla bla bla',
            event_type=talk,
            camp=camp1
        )
        ev2 = Event.objects.create(
            title='State of the world',
            abstract='abstract here, bla bla bla',
            event_type=keynote,
            camp=camp1
        )
        ev3 = Event.objects.create(
            title='Welcome to bornhack!',
            abstract='abstract here, bla bla bla',
            event_type=talk,
            camp=camp1
        )
        ev4 = Event.objects.create(
            title='bar is open',
            abstract='the bar is open, yay',
            event_type=facility,
            camp=camp1
        )
        ev5 = Event.objects.create(
            title='Network something',
            abstract='abstract here, bla bla bla',
            event_type=talk,
            camp=camp1
        )
        ev6 = Event.objects.create(
            title='State of outer space',
            abstract='abstract here, bla bla bla',
            event_type=talk,
            camp=camp2
        )
        ev7 = Event.objects.create(
            title='Welcome to bornhack!',
            abstract='abstract here, bla bla bla',
            event_type=talk,
            camp=camp2
        )
        ev8 = Event.objects.create(
            title='bar is open',
            abstract='the bar is open, yay',
            event_type=talk,
            camp=camp2
        )
        ev9 = Event.objects.create(
            title='The Alternative Welcoming',
            abstract='Why does The Alternative support BornHack? Why does The Alternative think IT is an overlooked topic? A quick runt-hrough of our program and workshops. We will bring an IT political debate to both the stage and the beer tents.',
            event_type=talk,
            camp=camp1
        )
        ev10 = Event.objects.create(
            title='Words and Power - are we making the most of online activism?',
            abstract='For years, big names like Ed Snowden and Chelsea Manning have given up their lives in order to protect regular people like you and me from breaches of our privacy. But we are still struggling with getting people interested in internet privacy. Why is this, and what can we do? Using experience from communicating privacy issues on multiple levels for a couple of years, I have encountered some deep seated issues in the way we talk about what privacy means. Are we good enough at letting people know whats going on?',
            event_type=keynote,
            camp=camp1
        )
        ev11 = Event.objects.create(
            title='r4d1o hacking 101',
            abstract='Learn how to enable the antenna part of your ccc badge and get started with receiving narrow band FM. In the workshop you will have the opportunity to sneak peak on the organizers radio communications using your SDR. If there is more time we will look at WiFi radar or your protocol of choice.',
            event_type=workshop,
            camp=camp1
        )
        ev12 = Event.objects.create(
            title='Introduction to Sustainable Growth in a Digital World',
            abstract='Free Choice is the underestimated key to secure value creation in a complex economy, where GDP-models only measure commercial profit and ignore the environment. We reconstruct the model thinking about Utility, Production, Security and Environment around the 5 Criteria for Sustainability.',
            event_type=workshop,
            camp=camp1
        )
        ev13 = Event.objects.create(
            title='American Fuzzy Lop and Address Sanitizer',
            abstract='''
We have powerful and easy to use tools that can vastly improve the quality and security of the code we use everyday.

Code written in C and C++ is often riddled with bugs in the memory management. Out of bounds accesses, use after free errors and other issues can hamper the security and stability of applications. Unfortunately many free software developers don't use freely available tools that easily allow finding and eliminating many of these bugs. The talk will encourage developers to change that and integrate these tools into their development process.

Slides: [https://www.int21.de/slides/bornhack2016-fuzzing/](https://www.int21.de/slides/bornhack2016-fuzzing/)
            ''',
            event_type=talk,
            camp=camp1
        )
        ev14 = Event.objects.create(
            title='PGP Keysigning Party',
            abstract='''
Let's verify each other's digital PGP keys at BornHack so that we can authenticate each other when we are not together at the island.

For people who haven't attended a PGP keysigning party before, we will guide you through it

### What do I need to bring?

1. Bring the output of `gpg --fingerprint $YOUR_KEY_ID` on some pieces of paper to hand out.
2. (Optional) Bring some government-issued identification paper (passport, drivers license, etc.). The ID should contain a picture of yourself. You can leave this out, but then it will be a bit harder for others to verify your key properly.
            ''',
            event_type=workshop,
            camp=camp1
        )
        ev15 = Event.objects.create(
            title='Bluetooth Low Energy',
            abstract='''
BLE provides versatile wireless communication at a very low
power consumption, especially compared to classic Bluetooth
and WiFi.

It has a wide range of uses where proximity detection is used
for a lot of applications such as alerting when a keychain
goes out of range or requesting alerts from lost objects.  Among
consumer products, Apple iBeacons is a notable application of
the technology.  However, it is also used for human input devices
such as mice and keyboards as well as various forms of sensors,
e.g. temperature, heart rate, etc.

BLE enables devices to run off coincell batteries for years
while retaining connections or doing periodic broadcasting.
This makes the technology appealing for the maker community
for applications that are power-constrained, e.g. due to having
a limited power-budget (say, running off a small PV-cell) or
running off a battery.

This talk explains how the low power consumption is achieved,
what the possible topologies are, and how this affects the types
of applications you can build on top.  Finally, a low-level
demonstration of interfacing with a BLE controller is performed.
            ''',
            event_type=talk,
            camp=camp1
        )
        ev16 = Event.objects.create(
            title='TLS attacks and the burden of faulty TLS implementations',
            abstract='''
TLS is by far the most important cryptographic protocol in use today.
In recent years TLS received much more attention from security
researchers. Implementation errors like Heartbleed and protocol bugs
like BEAST, Lucky Thirteen, DROWN and many more have made headlines.

Faulty implementations can enable attacks. In some cases they can even
be a security risk for uninvolved third parties and endanger the whole
TLS ecosystem. Especially so-called Enterprise devices that have their
own TLS stack are often a reason for concern.

The speaker will give an overview of implementation errors that
happened in various TLS stacks and will shed light on this
underappreciated problem.

Slides: [https://www.int21.de/slides/bornhack2016-tls/](https://www.int21.de/slides/bornhack2016-tls/)
            ''',
            event_type=talk,
            camp=camp1
        )
        ev17 = Event.objects.create(
            title='State of the Network',
            abstract='Come and meet the network team who will talk about the design and operation of the network at BornHack.',
            event_type=talk,
            camp=camp1
        )
        ev18 = Event.objects.create(
            title='Running Exit Nodes in the North',
            abstract='''
Tor is free software and an open network that helps you defend against
traffic analysis, a form of network surveillance that threatens personal
freedom and privacy, confidential business activities and relationships,
and state security.

People can donate their bandwidth to the Tor network and support human
rights. Many people in Finland have done this.

Especially Tor network needs fast exit nodes which are final nodes before
traffic reaches its destination. Because Tor traffic exits through these
relays, the IP address of the exit relay is interpreted as the source of
the traffic.

If a malicious user employs the Tor network to do something that might be
objectionable or illegal, the exit relay may take the blame. People who run
exit relays should be prepared to deal with complaints, copyright takedown
notices, and the possibility that their servers may attract the attention
of law enforcement agencies.

In Finland, Juha Nurmi has been establishing good relationships with ISPs
and law enforcement agencies to keep Finnish exit nodes online.
            ''',
            event_type=talk,
            camp=camp1
        )

        self.output("creating speakers...")
        sp1 = Speaker.objects.create(
            name='Henrik Kramse',
            biography='Henrik is an internet samurai working in internet and security around the world.',
            slug='henrik-kramshj',
            camp=camp1
        )
        sp1.events.add(ev5)
        sp2 = Speaker.objects.create(
            name='Thomas Tykling',
            biography='random danish hacker',
            slug='thomas-tykling',
            camp=camp1
        )
        sp2.events.add(ev3, ev1)
        sp3 = Speaker.objects.create(
            name='Alex Ahf',
            biography='functional alcoholic',
            slug='alex-ahf',
            camp=camp1
        )
        sp3.events.add(ev4, ev2)
        sp4 = Speaker.objects.create(
            name='Jesper Arp',
            biography='Representative from The Alternative with focus in data visualization.',
            slug='jesper-arp',
            camp=camp1
        )
        sp4.events.add(ev9)
        sp5 = Speaker.objects.create(
            name='Rolf Bjerre',
            biography='The green pirate',
            slug='rolf-bjerre',
            camp=camp1
        )
        sp5.events.add(ev9)
        sp6 = Speaker.objects.create(
            name='Emma Holten',
            biography='Emma Holten is a feminist and human rights activist. She is co-founder and editor of the standard critical magazine Friktion and also a student at the University of Copenhagen. She speaks in both national and global contexts of feminism, digital activism and why privacy on the internet is crucial to a democracy, where everyone is equal.',
            slug='emma-holten',
            camp=camp1
        )
        sp6.events.add(ev10)
        sp7 = Speaker.objects.create(
            name='Christoffer Jerkeby',
            biography='Hacker and phone phreaker from Stockholm bent on radio. Researching security and privacy in wireless protocols.',
            slug='christoffer-jerkeby',
            camp=camp1
        )
        sp7.events.add(ev11)
        sp8 = Speaker.objects.create(
            name='Stephan Engberg',
            biography='Stephan Engberg is a Computer Scientist specializing in Innovation Strategist working with Digital Business when he realized the Digital World is designed through our approach to security models and economic models. He then dedicated himself to Privacy/Security by Design in Open Business Innovation making numerous breakthroughs in security and engaged in EU research activities he was e.g. member of the Strategic Advisory Board for FP7 Security Research Roadmapping and started manufacturing of RFID computer chips based on Privacy by Design with zero-knowledge based computing in passive chips without battery or ultra-low memory and computational capabilities. In 2003, he was selected by an a transatlantic panel of researchers in ethics as a Moral Example in the Computer Profession.',
            slug='stephan-engberg',
            camp=camp1
        )
        sp8.events.add(ev12)
        sp9 = Speaker.objects.create(
            name='Hanno Böck',
            biography='''
Hanno Böck started the Fuzzing Project in 2014 as an effort to improve
the security of free software code. In May the Linux Foundation's Core
Infrastructure Initiative decided to fund this work. He is also
working as a freelance journalist and regularly writes about IT
security issues for various publications. He is the author of the
monthly Bulletproof TLS Newsletter.
            ''',
            slug='hanno-bock',
            camp=camp1
        )
        sp9.events.add(ev13, ev16)
        sp10 = Speaker.objects.create(
            name='Ximin Luo',
            biography='''
I'm Ximin Luo, a Debian Developer and security research engineer. I work on
secure protocols and decentralized systems. I prefer to use high-level checked
languages such as Rust, OCaml, or Haskell. I work for the Reproducible Builds
project and have previously worked for MEGA, Tor, Google and Freenet.

I also like music, cooking, sci-fi and cats, in an order indistinguishable from
a truly random sequence by a polynomial-time-bounded computational adversary.
            ''',
            slug='ximin-luo',
            camp=camp1
        )
        sp10.events.add(ev14)
        sp11 = Speaker.objects.create(
            name='Michael Knudsen',
            biography='''
Michael has been involved in various open source-related projects.
His dayjob involves writing firmware for a BT/wifi controller
for a semiconductor company.
            ''',
            slug='michael-knudsen',
            camp=camp1
        )
        sp11.events.add(ev15)
        sp12 = Speaker.objects.create(
            name='BornHack Network Team',
            biography='The team you won\'t notice if everything goes as it should. Please bring them rum or beer if they look too stressed.',
            slug='bornhack-network-team',
            camp=camp1
        )
        sp12.events.add(ev17)
        sp13 = Speaker.objects.create(
            name='Juha Nurmi',
            biography='''
Juha Nurmi (age 28) is the founder and project
leader of the Ahmia search engine project. He is a security researcher and
has been involved in numerous projects funded by both the commercial
and government spheres, including DARPA Memex project in the Silicon
Valley. Juha is also a noted lecturer and public speaker. Juha's work on
Ahmia has been in part sponsored by the Google Summer of Code.
            ''',
            slug='juha-nurmi',
            camp=camp1
        )
        sp13.events.add(ev18)

        self.output("creating eventinstances...")
        ei1 = EventInstance.objects.create(
            event=ev3,
            when=(
                timezone.datetime(2016, 8, 27, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 27, 13, 0, tzinfo=timezone.utc),
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
        ei15 = EventInstance.objects.create(
            event=ev9,
            when=(
                timezone.datetime(2016, 8, 30, 11, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 30, 11, 30, tzinfo=timezone.utc),
            )
        )
        ei16 = EventInstance.objects.create(
            event=ev10,
            when=(
                timezone.datetime(2016, 8, 30, 12, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 30, 13, 0, tzinfo=timezone.utc),
            )
        )
        ei17 = EventInstance.objects.create(
            event=ev12,
            when=(
                timezone.datetime(2016, 8, 30, 9, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 30, 11, 30, tzinfo=timezone.utc),
            )
        )
        ei18 = EventInstance.objects.create(
            event=ev11,
            when=(
                timezone.datetime(2016, 8, 31, 14, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 31, 16, 0, tzinfo=timezone.utc),
            )
        )
        ei19 = EventInstance.objects.create(
            event=ev18,
            when=(
                timezone.datetime(2016, 9, 2, 14, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 9, 2, 15, 0, tzinfo=timezone.utc),
            )
        )
        ei20 = EventInstance.objects.create(
            event=ev17,
            when=(
                timezone.datetime(2016, 9, 2, 16, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 9, 2, 17, 0, tzinfo=timezone.utc),
            )
        )
        ei21 = EventInstance.objects.create(
            event=ev15,
            when=(
                timezone.datetime(2016, 9, 1, 15, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 9, 1, 16, 0, tzinfo=timezone.utc),
            )
        )
        ei22 = EventInstance.objects.create(
            event=ev14,
            when=(
                timezone.datetime(2016, 8, 31, 21, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 31, 22, 0, tzinfo=timezone.utc),
            )
        )
        ei23 = EventInstance.objects.create(
            event=ev16,
            when=(
                timezone.datetime(2016, 9, 1, 14, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 9, 1, 15, 0, tzinfo=timezone.utc),
            )
        )
        ei24 = EventInstance.objects.create(
            event=ev13,
            when=(
                timezone.datetime(2016, 8, 31, 17, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 8, 31, 18, 0, tzinfo=timezone.utc),
            )
        )

        self.output("creating productcategories")
        transportation = ProductCategory.objects.create(
            name='Transportation',
            slug='transportation'
        )
        merchendise = ProductCategory.objects.create(
            name='Merchandise',
            slug='merchandise'
        )

        self.output("creating products")
        prod1 = Product.objects.create(
            category=transportation,
            name='PROSA bus transport (open for everyone)',
            slug='prosa-bus',
            price=125,
            description='PROSA is sponsoring a bustrip from Copenhagen to the venue and back.',
            available_in=(
                timezone.datetime(2016, 4, 30, 11, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 10, 30, 11, 30, tzinfo=timezone.utc),
            )
        )
        prod2 = Product.objects.create(
            category=transportation,
            name='PROSA bus transport (open for everyone)',
            slug='prosa-bus',
            price=125,
            description='PROSA is sponsoring a bustrip from Copenhagen to the venue and back.',
            available_in=(
                timezone.datetime(2016, 4, 30, 11, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 10, 30, 11, 30, tzinfo=timezone.utc),
            )
        )
        prod3 = Product.objects.create(
            category=merchendise,
            name='T-shirt (large)',
            slug='t-shirt-large',
            price=160,
            description='Get a nice t-shirt',
            available_in=(
                timezone.datetime(2016, 4, 30, 11, 0, tzinfo=timezone.utc),
                timezone.datetime(2016, 10, 30, 11, 30, tzinfo=timezone.utc),
            )
        )

        self.output("creating infocategories")
        info_cat1 = InfoCategory.objects.create(
            camp=camp1,
            headline='When is BornHack happening?',
            anchor='when'
        )
        info_cat2 = InfoCategory.objects.create(
            camp=camp1,
            headline='Travel Information',
            anchor='travel'
        )
        info_cat3 = InfoCategory.objects.create(
            camp=camp1,
            headline='Where do I sleep?',
            anchor='sleep'
        )

        self.output("creating infoitems")
        info_item1 = InfoItem.objects.create(
            category=info_cat1,
            headline='Opening',
            anchor='opening',
            body='BornHack 2016 starts saturday, august 27th, at noon (12:00). It will be possible to access the venue before noon if for example you arrive early in the morning with the ferry. But please dont expect everything to be ready before noon :)'
        )
        info_item2 = InfoItem.objects.create(
            category=info_cat1,
            headline='Closing',
            anchor='closing',
            body='BornHack 2016 ends saturday, september 3rd, at noon (12:00). Rented village tents must be empty and cleaned at this time, ready to take down. Participants must leave the site no later than 17:00 on the closing day (or stay and help us clean up).'
        )
        info_item3 = InfoItem.objects.create(
            category=info_cat2,
            headline='Public Transportation',
            anchor='public-transportation',
            body='''

From/Via Copenhagen

There are several ways to get to Bornholm from Copenhagen. A domestic plane departs from Copenhagen Airport, and you can get from Copenhagen Central station by either bus or train via Ystad or the Køge-Rønne ferry connection.

Plane (very fast, most expensive)
    You can check plane departures and book tickets at dat.dk. There are multiple departures daily. The flight takes approximately 25 minutes. 
Via Ystad (quick, cheap and easy, crosses Sweden border)
    You can drive over Øresundsbroen to Ystad or you can take the train/bus from Copenhagen Central Station. You can buy train and ferry ticket at dsb.dk (Type in "København H" and "Rønne Havn"). More information about the crossing. The crossing takes 1 hour 20 minutes. In total about 3 hours 15 minutes. Due to recent developments an ID (passport, drivers license or similar) is required when crossing the Denmark/Sweden border. 
Via Køge (cheap, slow)
    Take the S-train to Køge Station (you need an "all zones" ticket) or travel by car. The ferry terminal is within walking distance from the station. You can check out prices here. It takes approximately 1 hour to get to Køge. The crossing takes 5 hours 30 minutes. 

From Sweden/Malmö

To get to Bornholm from Malmö you may take a train from Malmö to Ystad and the ferry from Ystad to Bornholm.

Skånetrafiken runs trains from Malmö C to Ystad every 30 minutes. Trains leave at 08 and 38 minutes past the hour. Go to skanetrafiken for details.

The ferry from Ystad to Rønne leaves four times per day. Morning: 08:30-09:50 Noon: 12:30-13:50 Afternoon: 16:30-17:50 Evening: 20:30-21:50 Booking the ferry tickets prior to departure can drastically reduce the price. See "Getting from Rønne to the Venue" final step.
From Abroad

If you are going to BornHack from abroad you have different options as well.

Berlin (Germany)
    There are no public transport routes from Berlin to Mukran, Sassnitz ferry terminal on Saturdays, including Aug 27 and Sept 03 the Bornhack start/end dates. Your best bet is to get a train to Dubnitz, Sassnitz station. Unfortunately it is still 1.7km to the actual ferry terminal: map of route. There is a bus, but it only goes once a weekday at 12:28 and not at all on Weekends. You can of course take a taxi. Search for routes Berlin ‐ Dubnitz on bahn.de. At the time of writing, the best route is:
    08:45 Berlin Hbf → train with 2 changes, 50€ for a 2-way return ticket.
    12:52 Sassnitz → taxi, ~14€, 10 min.
    13:00 Mukran-Sassnitz ferry terminal
    If you want to try your luck at a direct route to the ferry terminal, search for routes Berlin ‐ Sassnitz-Mukran Fährhafen on bahn.de or for routes Berlin ‐ Fährhafen Sassnitz on checkmybus.com.
Sassnitz (Germany)
    There is a direct ferry taking cars going from Sassnitz ferry terminal which is 4km away from Sassnitz itself. The company is called BornholmerFærgen and the tickets cost 32€ (outgoing) and 25€ (return). It can also be booked from aferry.co.uk. The ferry departs for Bornholm on Aug 27 at 11:50, 13:30, and returns to Sassnitz on Sept 03 at 08:00, 09:00. Detailed timetable: English, Danish.
Kolobrzeg (Poland)
    There is a passenger ferry from Kolobrzeg to Nexø havn.

Getting from Rønne to the Venue

The venue is 24km from Rønne. We will have a shuttle bus that will pick people up and take them to the venue. It is also possible to take a public bus to near the venue. Local taxis can also get you here. The company operating on Bornholm is called Dantaxi and the local phonenumber is +4556952301.
            '''
        )
        info_item4 = InfoItem.objects.create(
            category=info_cat1,
            headline='Bus to and from BornHack',
            anchor='bus-to-and-from-bornhack',
            body='PROSA, the union of IT-professionals in Denmark, has set up a great deal for BornHack attendees travelling from Copenhagen to BornHack. For only 125kr, about 17 euros, you can be transported to the camp on opening day, and back to Copenhagen at the end of the camp!'

        )
        info_item5 = InfoItem.objects.create(
            category=info_cat1,
            headline='Driving and Parking',
            anchor='driving-and-parking',
            body='''
A car is very convenient when bringing lots of equipment, and we know that hackers like to bring all the things. We welcome cars and vans at BornHack. We have ample parking space very close (less than 50 meters) to the main entrance.

Please note that sleeping in the parking lot is not permitted. If you want to sleep in your car/RV/autocamper/caravan please contact us, and we will work something out.
            '''
        )
        info_item5 = InfoItem.objects.create(
            category=info_cat3,
            headline='Camping',
            anchor='camping',
            body='BornHack is first and foremost a tent camp. You need to bring a tent to sleep in. Most people go with some friends and make a camp somewhere at the venue. See also the section on Villages - you might be able to find some likeminded people to camp with.'
        )
        info_item6 = InfoItem.objects.create(
            category=info_cat3,
            headline='Cabins',
            anchor='cabins',
            body='We rent out a few cabins at the venue with 8 beds each for people who don\'t want to sleep in tents for some reason. A tent is the cheapest sleeping option (you just need a ticket), but the cabins are there if you want them.'
        )

        self.output("creating villages")
        vil1 = Village.objects.create(
            contact=user1,
            camp=camp1,
            name='Baconsvin',
            slug='baconsvin',
            description='The camp with the doorbell-pig! Baconsvin is a group of happy people from Denmark doing a lot of open source, and are always happy to talk about infosec, hacking, BSD, and much more. A lot of the organizers of BornHack live in Baconsvin village. Come by and squeeze the pig and sign our guestbook!'
        )
        vil2 = Village.objects.create(
            contact=user2,
            camp=camp1,
            name='NetworkWarriors',
            slug='networkwarriors',
            description='We will have a tent which house the NOC people, various lab equipment people can play with, and have fun. If you want to talk about networking, come by, and if you have trouble with the Bornhack network contact us.'
        )
        vil3 = Village.objects.create(
            contact=user3,
            camp=camp1,
            name='TheCamp.dk',
            slug='the-camp',
            description='This village is representing TheCamp.dk, an annual danish tech camp held in July. The official subjects for this event is open source software, network and security. In reality we are interested in anything from computers to illumination soap bubbles and irish coffee'
        )

        self.output("done!")

