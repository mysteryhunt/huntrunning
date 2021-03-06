from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from hunt.solving.models import Puzzle, Team, canonicalize, get_meta
from hunt.mh2012.models import ShowProduced
from hunt.solving.models import Solved

from datetime import datetime
import os
import json

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
            team = p.team
            if not p.point_released:
                solved_puzzles = Solved.objects.filter(team=team).count()
                shows_produced = ShowProduced.objects.filter(team=team, point_released=True).count()
                team.nsolved = solved_puzzles + shows_produced

                #points is actually cubic in number of unlocks, being as sum of
                #squares
                team.score = team.nsolved * (team.nsolved + 1) * (2 * team.nsolved + 1) / 6
                team.release()

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
                release_path = os.path.join(team.team_path, "letters_from_max_and_leo", "release.js")
                f = open(release_path + ".tmp", "w")
                puzzles = [Puzzle.objects.get(title=p.round) for p in ShowProduced.objects.filter(team=p.team).order_by('release_at')]
                releases = [[puzzle.title, canonicalize(puzzle.title)] for puzzle in puzzles]
                releases = [['Greetings from Max', 'greetings_from_max']] + releases
                print >>f, "this.letters_from_max_and_leo=" + json.dumps(releases)
                f.close()
                os.rename(release_path + ".tmp", release_path)

