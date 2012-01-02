from hunt.solving.models import *
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required


class RoundStatus:
    def __init__(self):
        self.meta_solved = False
        self.puzzles_solved = 0
        self.puzzles_total = 0
        self.matrixed_puzzles_solved = 0
        self.matrixed_puzzles_total = 0

@staff_member_required
def board(request):

    teams = list(Team.objects.all())
    #get team-meta matrix

    metas = Puzzle.objects.filter(is_meta=True).order_by('round')

    solves = Solved.objects.all()

    team_round_solves = dict((team, dict((meta.round, RoundStatus()) for meta in metas)) for team in teams)

    puzzles = list(Puzzle.objects.all())

    for solve in solves:
        team_solves = team_round_solves[solve.team]
        puzzle = solve.puzzle
        round = team_solves[puzzle.round]

        if puzzle.is_meta:
            round.meta_solved = True
        else:
            round.puzzles_solved += 1


        if puzzle.matrixed_round:
            matrixed_round = team_solves[puzzle.matrixed_round]
            matrixed_round.matrixed_puzzles_solved += 1

    for team in teams:
        team_solves = team_round_solves[team]
        for puzzle in puzzles:
            team_solves[puzzle.round].puzzles_total += 1
            if puzzle.matrixed_round:
                team_solves[puzzle.matrixed_round].matrixed_puzzles_total += 1


    return render_to_response("board.html", locals(),
                              RequestContext(request, {}))

