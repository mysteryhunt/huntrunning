from django.db.models import F
from django.conf import settings
from django.http import HttpResponse

from django.shortcuts import render_to_response
from django.template import RequestContext

from hashlib import md5
from hunt.solving.models import *

import base64
import Crypto.Cipher.AES as aes


def get_team(request):
    team = request.META.get('REMOTE_USER', None)
    if team is None:
        raise RuntimeError("no team")
    team = Team.objects.get(id=team)
    return team

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

def award(request):
    team = get_team(request)
    encoded_token = str(request.GET["t"])
    token = base64.urlsafe_b64decode(encoded_token + "==")

    #why reencode what I just decoded?  Because b64 allows
    #multiple encodings of the same data (really!), and we
    #need the canonical encoding
    encoded_token = base64.urlsafe_b64encode(token)[:-1]

    #has token been used yet?
    if EventPointToken.objects.filter(token=encoded_token).count():
        return HttpResponse("Already used or invalid")

    encryptor = aes.new(md5(settings.SECRET_KEY).digest())
    result = encryptor.decrypt(token)
    try:
        points = int(result[:4])
    except:
        return HttpResponse("Already used or invalid")

    EventPointToken(team=team, token=encoded_token).save()
    response = "OK, event points added.  You now have %s %r" % (team.event_points + points, encoded_token)
    Team.objects.filter(id=team.id).update(event_points=F('event_points') + points)
    return HttpResponse(response)

def show_callin(request, extra={}):

    team = get_team(request)
    puzzle = Puzzle.objects.get(id=request.REQUEST["puzzle"])

    solved = Solved.objects.filter(team=team,puzzle=puzzle).count()
    if solved:
        answer = puzzle.answer
    else:
        past_answers = AnswerRequest.objects.filter(team=team, puzzle=puzzle)

    locals().update(extra)

    return render_to_response('callin.html', locals(), context_instance=RequestContext(request))

def do_callin(request):
    team = get_team(request)
    puzzle_id = request.POST["puzzle"]
    puzzle = Puzzle.objects.get(id=puzzle_id)
    phone = Phone.objects.get(id=request.REQUEST['phone'])
    if phone.team != team:
        return
    if request.POST['action'].startswith('Buy'):
        #buy an answer
        if team.event_points < team.answer_event_point_cost:
            message = "Not enough points"
            return show_callin(request, dict(message=message, puzzle=puzzled))
        else:
            team.event_points -= team.answer_event_point_cost
            team.save()
            AnswerRequest(team=team,
                          puzzle=puzzle,
                          answer=puzzle.answer,
                          answer_normalized=puzzle.answer_normalized,
                          bought_with_event_points=True,
                          phone=phone).save()
    else:

        answer = request.POST['answer']
        answer_normalized = normalize_answer(answer)
        if AnswerRequest.objects.filter(team=team, puzzle=puzzle, answer_normalized=answer_normalized).count() > 0:
            message = "Already called in!"
            return show_callin(request, dict(message=message, puzzle=puzzle))

        backsolve = 'backsolve' in request.POST
        AnswerRequest(team=team,
                      puzzle=puzzle,
                      answer=answer,
                      answer_normalized=answer_normalized,
                      backsolve=backsolve,
                      phone=phone).save()

    queuelength = AnswerRequest.objects.filter(handled=False).count()
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
    phone = Phone.objects.get(id=request.REQUEST['phone'])
    if phone.team != team:
        return
    CallRequest(team=team, queue=queue, reason=reason, phone=phone).save()
    queuelength = CallRequest.objects.filter(handled=False).count()
    return render_to_response('general-received.html', locals(), context_instance=RequestContext(request))
