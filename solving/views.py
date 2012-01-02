from django.conf import settings
from django.http import HttpResponse

from django.shortcuts import render_to_response
from django.template import RequestContext

from hunt.solving.models import *

def get_team(request):
    team = request.META.get('REMOTE_USER', None)
    if team is None:
        raise RuntimeError("no team")
    team = Team.objects.get(id=team)
    return team

def points(request):
    js = "points(%d);" % get_team(request).score
    return HttpResponse(js, content_type="application/javascript")

def general(request):
    if request.method == "GET":
        return show_general(request)
    else:
        return do_general(request)

def callin(request):
    if request.method == "GET":
        return show_callin(request)
    else:
        return do_callin(request)

def show_callin(request, extra={}):
    team = get_team(request)
    puzzle = Puzzle.objects.get(id=request.REQUEST["puzzle"])
    past_answers = AnswerRequest.objects.filter(team=team, puzzle=puzzle)

    locals().update(extra)

    return render_to_response('callin.html', locals(), context_instance=RequestContext(request))

def do_callin(request):
    team = get_team(request)
    puzzle_id = request.POST["puzzle"]
    puzzle = Puzzle.objects.get(id=puzzle_id)

    if request.POST['action'].startswith('Buy'):
        #buy an answer
        if team.event_points < team.answer_event_point_cost:
            message = "Not enough points"
            return show_callin(request, dict(message=message, puzzle=puzzled))
        else:
            team.event_points -= team.answer_event_point_cost
            team.save()
            AnswerRequest(team=team, puzzle=puzzle, answer=puzzle.answer,answer_normalized=puzzle.answer_normalized, bought_with_points=True).save()
    else:

        answer = request.POST['answer']
        answer_normalized = normalize_answer(answer)
        if AnswerRequest.objects.filter(team=team, puzzle=puzzle, answer_normalized=answer_normalized).count() > 0:
            message = "Already called in!"
            return show_callin(request, dict(message=message, puzzle=puzzle))

        backsolve = 'backsolve' in request.POST
        AnswerRequest(team=team, puzzle=puzzle, answer=answer,answer_normalized=answer_normalized, backsolve=backsolve).save()
    return render_to_response('called.html', locals(), context_instance=RequestContext(request))


def show_general(request, extra={}):
    team = get_team(request)
    locals().update(extra)
    queues = QUEUES
    return render_to_response('general.html', locals(), context_instance=RequestContext(request))

def do_general(request):
    team = get_team(request)
    queue = request.POST['queue']
    reason = request.POST['reason']
    CallRequest(team=team, queue=queue, reason=reason).save()
    return render_to_response('general-received.html', locals(), context_instance=RequestContext(request))
