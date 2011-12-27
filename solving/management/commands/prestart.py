from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team

import crypt
import os
import random
import string

SALT_VALUES=string.letters + string.digits

class Command(BaseCommand):
    help = """Prestarts the hunt, by creating a directory structure and 
htaccess file for each team and inserting a bogus index.html.

This command will overwrite the htpasswd file but not index
files.
"""

    def handle(self, *args, **options):
        htpasswd_file = open(settings.HTPASSWD_PATH, "w")

        for team in Team.objects.all():
            team_path = os.path.join(settings.TEAM_PATH, team.id)
            try:
                os.mkdir(team_path)
            except OSError:
                pass
            index_path = os.path.join(team_path, 'index.html')
            if not os.path.exists(index_path):
                f = open(index_path, 'w')
                f.write("""<html><head><title>Hunt</title></head><body>It works!  You don't need to contact HQ: your password seems to be working fine.  Watch this space.</body></html>""")
                f.close()

            salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
            htpasswd_file.write("%s:%s\n" % (team.id, crypt.crypt(team.password, salt)))

        salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
        htpasswd_file.write("%s:%s\n" % (settings.ADMIN_NAME, crypt.crypt(settings.ADMIN_PASSWORD, salt)))
        htpasswd_file.close()
