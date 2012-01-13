from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team, Meta, UnlockBatch, TeamUnlock
from hunt.common import safe_link
from hunt.solving.password import write_htpasswd

import hashlib
import hmac
import json
import os
import string
import sys
from time import time

banned_filenames = ["solved.js", "team-data.js", ".htaccess", "release.js"]
shared_directories = ["memos_from_the_management", "events"]

def hmac_with_server_key(s):
    return hmac.new(settings.APPENGINE_SERVER_KEY, s, hashlib.sha1).hexdigest()

class Command(BaseCommand):
    help = """Starts the hunt, by creating a directory structure and 
htaccess file for each team and setting up the initial index.html.

Also, release the first batch of puzzles

This command will overwrite the htpasswd file and index files.
"""

    def handle(self, *args, **options):
        now = str(int(time()))
        try:
            meta = Meta.objects.get(key="start_time")
            meta.value = now
        except:
            meta = Meta(key="start_time", value=now)

        meta.save()

        htaccess_path = os.path.join(settings.PUZZLE_PATH, ".htaccess")
        if os.path.exists(htaccess_path):
            base_htaccess = open(htaccess_path).read()
        else:
            base_htaccess=""

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
                    continue

                team_file_path = os.path.join(team_path, filename)

                safe_link(path, team_file_path)
            team.release()

            #appengine stuff
            team_file_path = os.path.join(team_path, "team-data.js")
            f = open(team_file_path, "w")
            print >>f, "TEAM_NAME = %s;" % json.dumps(team.id)
            print >>f, "TEAM_AUTH = %s;" % json.dumps(hmac_with_server_key("team:"+team.id))
            f.close()

            letters_path = os.path.join(team_path, "letters_from_max_and_leo")
            if not os.path.exists(letters_path):
                os.mkdir(letters_path)
            release_path = os.path.join(letters_path, "release.js")
            f = open(release_path, "w")
            print >>f, """
            this.letters_from_max_and_leo = [
                ['Greetings from Max', 'greetings_from_max']
                ];
            """
            f.close()

            # create new .htacces file

            team_htaccess_path = os.path.join(team_path, ".htaccess")
            htaccess_file = open(team_htaccess_path, "w")
            print >>htaccess_file, """%s
AuthUserFile %s
AuthName "Mystery Hunt"
AuthType Basic
Require User %s""" % (base_htaccess, settings.HTPASSWD_PATH, team.id)
            htaccess_file.close()

            #solved.js, empty
            team_solved_path = os.path.join(team_path, "solved.js")
            solved_file = open(team_solved_path, "w")
            print >>solved_file, "var puzzle_solved = {};"
            solved_file.close()

        write_htpasswd()
