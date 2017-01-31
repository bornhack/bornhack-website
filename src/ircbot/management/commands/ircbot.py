from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from time import sleep
import irc3, sys, asyncio


class Command(BaseCommand):
    args = 'none'
    help = 'Runs the BornHack IRC bot to announce talks and manage team channel permissions'

    def output(self, message):
        self.stdout.write('%s: %s' % (timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message))

    def handle(self, *args, **options):
        self.output('IRC bot worker running...')
        # connect to IRC
        config = {
            'nick': settings.IRCBOT_NICK,
            'autojoins': [settings.IRCBOT_SCHEDULE_ANNOUNCE_CHANNEL],
            'host': settings.IRCBOT_SERVER_HOSTNAME,
            'port': settings.IRCBOT_SERVER_PORT,
            'ssl': settings.IRCBOT_SERVER_USETLS,
            'timeout': 30,
            'includes': [
                'ircbot.irc3module',
            ],
        }
        irc3.IrcBot(**config).run(forever=True)

