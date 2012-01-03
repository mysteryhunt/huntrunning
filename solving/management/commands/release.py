from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import get_meta, Team
from hunt.common import safe_link

import os

class Command(BaseCommand):
    help = """Intended to be run every minute to unlock puzzles that teams
should have access to due to time release.
"""

    def handle(self, *args, **options):
        if not get_meta('start_time'):
            return #nothing to do as hunt is not yet started

        for team in Team.objects.all():
            team.release()
