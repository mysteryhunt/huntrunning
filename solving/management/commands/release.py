from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team
from hunt.common import safe_link

import os

class Command(BaseCommand):
    help = """Release puzzles up to a given score level
"""
    args = 'release_score_level'

    def handle(self, *args, **options):
        if len(args) == 0:
            print "Must provide a score level to release up to"
            return
        new_score = int(args[0])

        for team in Team.objects.all():
            team.release(team.score, new_score)
