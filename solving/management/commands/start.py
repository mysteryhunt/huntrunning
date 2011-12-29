from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team
from hunt.common import safe_link

import crypt
import os
import random
import string

SALT_VALUES=string.letters + string.digits

class Command(BaseCommand):
    help = """Starts the hunt, by creating a directory structure and 
htaccess file for each team and setting up the initial index.html.

Also, release the first batch of puzzles

This command will overwrite the htpasswd file and index files.
"""

    def handle(self, *args, **options):
        htpasswd_file = open(settings.HTPASSWD_PATH, "w")

        for team in Team.objects.all():
            team_path = os.path.join(settings.TEAM_PATH, team.id)
            try:
                os.mkdir(team_path)
            except OSError:
                pass
            
            #FIXME: need to figure out what files will be linked --
            #ideally, this will probably be a whole directory
            for filename in ["index.html"]:
                index_path = os.path.join(settings.PUZZLE_PATH, filename)
                team_index_path = os.path.join(team_path, filename)
            
                safe_link(index_path, team_index_path)

            team.release(-1, 0)

            salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
            htpasswd_file.write("%s:%s\n" % (team.id, crypt.crypt(team.password, salt)))

        salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
        htpasswd_file.write("%s:%s\n" % (settings.ADMIN_NAME, crypt.crypt(settings.ADMIN_PASSWORD, salt)))
        htpasswd_file.close()
