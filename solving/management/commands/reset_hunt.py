from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import *

import os
import subprocess

class Command(BaseCommand):
    help = """Reset the hunt status"""

    def handle(self, *args, **options):
        Solved.objects.all().delete()
        TeamUnlock.objects.all().delete()
        CallRequest.objects.all().delete()
        AnswerRequest.objects.all().delete()
        EventPointToken.objects.all().delete()

        for team in Team.objects.all():
            team.score = 0
            team.nsolves = 0
            team.event_points = 0
            team.save()

            team_release_path = os.path.join(settings.TEAM_PATH, team.id)
            if len(team_release_path) < 10:
                #this might be unsafe
                print "possibly unsafe to remove " + team_release_path
                return

            if os.path.exists(team_release_path):
                subprocess.call(["rm", "-rf", team_release_path])

        Meta.objects.all().delete()
