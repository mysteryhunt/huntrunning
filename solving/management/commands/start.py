from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team, Meta, UnlockBatch, TeamUnlock
from hunt.common import safe_link

import crypt
import hashlib
import hmac
import json
import os
import random
import string
import sys
from time import time

SALT_VALUES=string.letters + string.digits

banned_filenames = ["solved.js", "team-data.js"]
shared_directories = ["letters"]

def hmac_with_server_key(s):
    return hmac.new(settings.APPENGINE_SERVER_KEY, s, hashlib.sha1).hexdigest()

class Command(BaseCommand):
    help = """Starts the hunt, by creating a directory structure and 
htaccess file for each team and setting up the initial index.html.

Also, release the first batch of puzzles

This command will overwrite the htpasswd file and index files.
"""

    def handle(self, *args, **options):
        htpasswd_file = open(settings.HTPASSWD_PATH + ".tmp", "w")

        now = str(int(time()))
        try:
            meta = Meta.objects.get(key="start_time")
            meta.value = now
        except:
            meta = Meta(key="start_time", value=now)

        meta.save()

        n_batches = UnlockBatch.objects.order_by("batch").count()
        if not n_batches:
            print >>sys.stderr, "Need some unlock batches to start the hunt"
            return

        for team in Team.objects.all():
            team_path = os.path.join(settings.TEAM_PATH, team.id)
            try:
                os.mkdir(team_path)
            except OSError:
                pass

            #FIXME: need to figure out what files will be linked --
            #ideally, this will probably be a whole directory
            for filename in os.listdir(settings.PUZZLE_PATH):
                path = os.path.join(settings.PUZZLE_PATH, filename)
                if os.path.isdir(path) and filename not in shared_directories:
                    continue
                if filename in banned_filenames:
                    pass

                team_file_path = os.path.join(team_path, filename)

                safe_link(path, team_file_path)

            team.release()

            #appengine stuff
            team_file_path = os.path.join(team_path, "team-data.js")
            f = open(team_file_path, "w")
            print >>f, "TEAM_NAME = %s;" % json.dumps(team.id)
            print >>f, "TEAM_AUTH = %s;" % json.dumps(hmac_with_server_key("team:"+team.id))
            f.close()

            # htpasswd stuff
            salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
            htpasswd_file.write("%s:%s\n" % (team.id, crypt.crypt(team.password, salt)))

        salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
        htpasswd_file.write("%s:%s\n" % (settings.ADMIN_NAME, crypt.crypt(settings.ADMIN_PASSWORD, salt)))
        htpasswd_file.close()

        os.rename(settings.HTPASSWD_PATH + ".tmp", settings.HTPASSWD_PATH)
