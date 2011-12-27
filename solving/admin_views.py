from hunt.solving.models import *
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required


class RoundStatus:
    def __init__(self):
        self.meta_solved = False
        self.puzzles_solved = 0

@staff_member_required
def board(request):

    teams = Team.objects.all()
    #get team-meta matrix

    metas = Puzzle.objects.filter(is_meta=True).order_by('round')

    solves = Solved.objects.all()

    team_round_solves = dict((team, dict((meta.round, RoundStatus()) for meta in metas)) for team in teams)

    for solve in solves:
        team_solves = team_round_solves[solve.team]
        puzzle = solve.puzzle
        round = team_solves[puzzle.round]

        if puzzle.is_meta:
            round.meta_solved = True
        else:
            round.puzzles_solved += 1


    return render_to_response("board.html", locals(),
                              RequestContext(request, {}))

