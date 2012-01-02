from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from hunt.common import safe_link, safe_unlink

import os
import re

class Team(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    score = models.IntegerField(default=0)
    event_points = models.IntegerField(default=0)
    unlocked = models.IntegerField(default=0)

    @property
    def answer_event_point_cost(self):
        return 100

    def __unicode__(self):
        return self.name

    def puzzles_solved(self):
        return self.solved_set.filter(puzzle__is_meta__exact=False).count()

    def release(self, old_score, new_score):
        unlocked = UnlockBatch.objects.filter(points_required__gt = old_score).filter(points_required__lte = new_score).order_by('points_required')
        batch = None
        for batch in unlocked:
            puzzles = Puzzle.objects.filter(unlock_batch=batch.batch)
            for puzzle in puzzles:
                self.release_puzzle(puzzle)

        if batch:
            #install the release JS file for the latest batch

            release_path = os.path.join(settings.PUZZLE_PATH, "release-%s.js" % batch.batch)
            team_release_path = os.path.join(settings.TEAM_PATH, self.id, "release.js")

            safe_link(release_path, team_release_path)

    def release_puzzle(self, puzzle):
        puzzle_path = os.path.join(settings.PUZZLE_PATH, puzzle.path)
        team_puzzle_path = os.path.join(settings.TEAM_PATH, self.id, puzzle.path)
        safe_link(puzzle_path, team_puzzle_path)

    def unrelease_puzzle(self, puzzle):
        team_puzzle_path = os.path.join(settings.TEAM_PATH, self.id, puzzle.path)
        safe_unlink(team_puzzle_path)


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
    answer = models.CharField(max_length=100)
    answer_normalized = models.CharField(max_length=100)
    puzzle = models.ForeignKey('Puzzle')
    bought_with_points = models.BooleanField(default=False)
    backsolve = models.BooleanField(default=False)
    handled = models.BooleanField(default=False)
    correct = models.BooleanField(default=False)

@receiver(pre_save, sender=AnswerRequest)
def correct(instance=None, **kwargs):
    request = instance
    request.correct = request.answer_normalized == normalize_answer(request.puzzle.answer)


@receiver(post_save, sender=AnswerRequest)
def post_save_puzzle(sender, instance=None, **kwargs):
    team = instance.team
    puzzle = instance.puzzle
    if instance.handled == True and instance.correct() == True and not Solved.objects.filter(team=team, puzzle = puzzle).count():
        solved = Solved(team = team, puzzle = puzzle,
                        bought_with_event_points = False)
        solved.save()
        do_unlock(instance)

def do_unlock(answer_request):
    puzzle = answer_request.puzzle
    team = answer_request.team

    old_score = team.score

    if puzzle.is_meta:
        team.score += 3
    else:
        team.score += 1
    team.save()
    team.release(old_score, team.score)

class Puzzle(models.Model):
    #this is a hash of the pony name
    id = models.CharField(max_length=100, primary_key=True)

    #and this is the puzzle's real title
    title = models.CharField(max_length=100)
    round = models.CharField(max_length=100)

    #this only supports one reuse per puzzle, but that would be
    #easy to fix
    matrixed_round = models.CharField(max_length=100)

    answer = models.CharField(max_length=100)
    is_meta = models.BooleanField()
    unlock_batch = models.IntegerField()

    def __unicode__(self):
        return self.title

    @property
    def path(self):
        return os.path.join(canonicalize(self.round), canonicalize(self.title))

    @property
    def answer_normalized(self):
        return normalize_answer(self.answer)


@receiver(post_save, sender=AnswerRequest)
def fixup_puzzle(sender, instance=None, **kwargs):
    """Delete and re-release the puzzle where necessary"""

    if not instance.id:
        return #nothing to do for new puzzles

    old_puzzle = Puzzle.objects.get(id=instance.id)

    batch = UnlockBatch.objects.filter(batch=instance.unlock_batch)
    points = batch.points
    for team in teams:
        if team.score >= points:
            #the puzzle needs to be pulled and re-released for this team
            team.unrelease(old_puzzle)
            team.release(instance)

class UnlockBatch(models.Model):
    batch = models.IntegerField()
    points_required = models.IntegerField()

    class Meta:
        verbose_name_plural = "Unlock Batches"

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
def normalize_answer(answer):
    import re
    forbidden_re = re.compile("[^A-Z]")
    return re.sub(forbidden_re, "", answer.upper())

def canonicalize(title):
    """Convert a possibly-complicated title to a reasonable path name."""
    # suppress 's
    title = re.sub(u"['\u2019]([st])\\b", r'\1', title) # possessives
    return re.sub(r'[^a-z0-9]+', '_', title.lower().strip()).strip('_')
