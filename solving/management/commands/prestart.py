from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team
from hunt.solving.password import write_htpasswd

from time import time

import os

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

        index_tmpl_file = os.path.join(os.path.dirname(__file__), "prestart-index.html")
        index = open(index_tmpl_file).read()
        index = index.replace("{START_TIME}", str(start_in + int(time())))

        htaccess_path = os.path.join(settings.PUZZLE_PATH, ".htaccess")
        if os.path.exists(htaccess_path):
            base_htaccess = open(htaccess_path).read()
        else:
            base_htaccess=""

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

            team_htaccess_path = os.path.join(team_path, ".htaccess")
            htaccess_file = open(team_htaccess_path, "w")
            print >>htaccess_file, """%s
AuthUserFile %s
AuthName "Mystery Hunt"
AuthType Basic
Require User %s""" % (base_htaccess, settings.HTPASSWD_PATH, team.id)
            htaccess_file.close()

        write_htpasswd()
