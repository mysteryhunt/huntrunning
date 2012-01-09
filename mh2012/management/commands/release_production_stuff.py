from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Puzzle
from hunt.mh2012.models import ShowProduced

from datetime import datetime

class Command(BaseCommand):
    help = """Release puzzles and points for productions"""

    def handle(self, *args, **options):
        now = datetime.now()
        produced = ShowProduced.objects.filter(release_at__lt = now,
                                                     puzzle_released=False)
        for p in produced:
            if not p.point_released:
                produced.team.update(nsolved=F('nsolved') + 1, score=F('score') + (F('nsolved') + 1) * (F('nsolved') + 1))
                p.point_released = True
            if not p.puzzle_released and not p.do_not_release_puzzle_yet:
                p.puzzle_released = True
                puzzle = Puzzle.objects.get(round="Letters", puzzle=p.round)
                team.release(puzzle)
