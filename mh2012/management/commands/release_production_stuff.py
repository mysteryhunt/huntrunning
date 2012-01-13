from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from hunt.solving.models import Puzzle, Team, canonicalize, get_meta
from hunt.mh2012.models import ShowProduced

from datetime import datetime
import os

class Command(BaseCommand):
    help = """Release puzzles and points for productions"""

    def handle(self, *args, **options):
        if not get_meta('start_time'):
            return

        now = datetime.now()
        produced = ShowProduced.objects.filter(release_at__lt = now,
                                                     puzzle_released=False)
        for p in produced:
            should_save = False
            if not p.point_released:
                Team.objects.filter(id=p.team.id).update(nsolved=F('nsolved') + 1, score=F('score') + (F('nsolved') + 1) * (F('nsolved') + 1))
                p.point_released = True
                should_save = True
            if not p.puzzle_released and not p.do_not_release_puzzle_yet:
                p.puzzle_released = True
                puzzle = Puzzle.objects.get(round="Letters from Max and Leo", title=p.round)
                p.team.release_puzzle(puzzle)
                should_save = True
            if should_save:
                p.save()
                #generate letters/release.js
                release_path = os.path.join(p.team.team_path, "letters_from_max_and_leo", "release.js")
                f = open(release_path + ".tmp", "w")
                print >>f, json.dumps([[puzzle.title, canonicalize(puzzle.title)] for puzzle in ShowsProduced.objects.filter(team=p.team)])
                f.close()
                os.rename(release_path + ".tmp", release_path)

