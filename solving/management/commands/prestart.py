from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team

from time import time

import crypt
import os
import random
import string

SALT_VALUES=string.letters + string.digits

class Command(BaseCommand):
    help = """Prestarts the hunt, by creating a directory structure and 
htaccess file for each team and inserting a countdown index.html.

This command will overwrite the htpasswd file but not index
files.
"""

    def handle(self, *args, **options):
        if not len(args):
            print "Usage: mange.py prestart [Time in minutes until the hunt starts]"
            return

        start_in = args[0] #interpreted as minutes
        start_in = int(start_in) * 60

        htpasswd_file = open(settings.HTPASSWD_PATH, "w")

        index_tmpl_file = os.path.join(os.path.dirname(__file__), "prestart-index.html")
        index = open(index_tmpl_file).read()
        index = index.replace("{START_TIME}", str(start_in + int(time())))

        for team in Team.objects.all():
            team_path = os.path.join(settings.TEAM_PATH, team.id)
            try:
                os.mkdir(team_path)
            except OSError:
                pass
            index_path = os.path.join(team_path, 'index.html')
            if not os.path.exists(index_path):
                f = open(index_path, 'w')
                f.write(index)
                f.close()

            salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
            htpasswd_file.write("%s:%s\n" % (team.id, crypt.crypt(team.password, salt)))

        salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
        htpasswd_file.write("%s:%s\n" % (settings.ADMIN_NAME, crypt.crypt(settings.ADMIN_PASSWORD, salt)))
        htpasswd_file.close()
