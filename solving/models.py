from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

import os

class Team(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    score = models.IntegerField(default=0)
    unlocked = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

    def puzzles_solved(self):
        return self.solved_set.filter(puzzle__is_meta__exact=False).count()

QUEUES = [("Errata", "errata"), ("General", "general"), ("Pick up", "objects"), ("Puzzle-specific request(provide exact puzzle name and exact phrase describing why you are making this request)", "puzzle"), ("Production", "production")]

class CallRequest(models.Model):
    team = models.ForeignKey('Team')
    time = models.DateTimeField(auto_now=True)
    queue = models.CharField(choices=QUEUES, max_length=100)
    handled = models.BooleanField(default=False)
    reason = models.TextField(max_length=1000)

class AnswerRequest(models.Model):
    team = models.ForeignKey('Team')
    time = models.DateTimeField(auto_now=True)
    puzzle = models.ForeignKey('Puzzle')
    answer = models.CharField(max_length=100)
    answer_normalized = models.CharField(max_length=100)
    handled = models.BooleanField(default=False)

    def correct(self):
        if self.answer_normalized == normalize(self.puzzle.answer):
            return True
        else:
            return False

    correct.boolean = True

@receiver(post_save, sender=AnswerRequest)
def post_save(sender, instance=None, **kwargs):

    if instance.handled == True and instance.correct() == True:
        solved = Solved(team = instance.team, puzzle = instance.puzzle, 
                        bought_with_event_points = False)
        solved.save()
        do_unlock(instance)

def unlock_puzzle(team):
    team.score += 1
    puzzle = Puzzle.objects.get(unlock_order = team.score)
    puzzle_path = os.path.join(settings.PUZZLE_PATH, puzzle.path)
    team_puzzle_path = os.path.join(settings.TEAM_PATH, team.id, puzzle.path)
    os.link(puzzle_path, team_puzzle_path)

    #we also need to change the puzzle index pages
    #if the unlocked puzzle is a meta, we need to change the root
    #index.  It looks like cscott has code for this on ihtfp.us, and 
    #so I'm going to ignore it for now

def do_unlock(answer_request):
    #so, this doesn't really account for unlock batches yet.
    puzzle = answer_request.puzzle
    if puzzle.is_meta:
        for i in range(3):
            unlock_puzzle(answer_request.team)
    else:
        unlock_puzzle(answer_request.team)

class Puzzle(models.Model):
    title = models.CharField(max_length=100, primary_key=True)
    path = models.CharField(max_length=100)
    round = models.IntegerField()
    answer = models.CharField(max_length=100)
    is_meta = models.BooleanField()
    unlock_order = models.IntegerField()

    def __unicode__(self):
        return self.title

class Solved(models.Model):
    team = models.ForeignKey('Team')
    puzzle = models.ForeignKey('Puzzle')
    time = models.DateTimeField(auto_now=True)
    bought_with_event_points = models.BooleanField()

    unique_together = (("team", "puzzle"),)

class PhysicalObject(models.Model):
    """Physical puzzle components"""
    name = models.CharField(max_length=100, primary_key=True)

    def __unicode__(self):
        return self.name

class PhysicalObjectDistribution(models.Model):
    """A team has been given the object"""
    team = models.ForeignKey('Team')
    physical_object = models.ForeignKey('PhysicalObject')
    time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("team", "physical_object")

#this places strong limits on what answers are possible.
def normalize(answer):
    import re
    forbidden_re = re.compile("[^A-Z]")
    return re.sub(forbidden_re, "", answer.upper())
