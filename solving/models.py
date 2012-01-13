from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from hunt.common import safe_link, safe_unlink, safe_mkdirs
from time import time

import os
import re
import json

class Meta(models.Model):
    key = models.CharField(max_length=50, primary_key=True)
    value = models.CharField(max_length=100)

def get_meta(k):
    try:
        return Meta.objects.get(key=k).value
    except:
        return None

class Team(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    score = models.IntegerField(default=0)
    event_points = models.IntegerField(default=0)
    nsolved = models.IntegerField(default=0)

    class Meta:
        ordering = ['name']

    @property
    def answer_event_point_cost(self):
        return 100

    def __unicode__(self):
        return self.name

    def puzzles_solved(self):
        return self.solved_set.filter(puzzle__is_meta__exact=False).count()

    def release(self):
        """Release any puzzles that should be unlocked as-of now"""
        now = time()
        #get the hunt start time
        start_time = get_meta('start_time')
        if start_time is None:
            return None
        start_time = int(start_time)

        #get the most-recently-unlocked batch
        latest_unlock = list(TeamUnlock.objects.filter(team=self).order_by('-batch__batch')[:1])

        if latest_unlock:
            last_batch = latest_unlock[0].batch.batch
        else:
            last_batch = 0

        #get the remaining unlocks
        remaining_batches = list(UnlockBatch.objects.filter(batch__gt=last_batch).order_by('batch'))

        any_unlocked = False
        last_batch = None
        for batch in remaining_batches:
            unlock_time = start_time + batch.base_time - batch.minutes_early_per_point * self.score * 60
            if unlock_time > now:
                break

            TeamUnlock(team=self, batch=batch).save()

            puzzles = Puzzle.objects.filter(unlock_batch=batch.batch)
            for puzzle in puzzles:
                self.release_puzzle(puzzle)
            any_unlocked = True
            last_batch = batch

        if any_unlocked:
            #install the release JS file for the latest batch

            release_path = os.path.join(settings.PUZZLE_PATH, "release-%s.js" % last_batch.batch)
            team_release_path = os.path.join(settings.TEAM_PATH, self.id, "release.js")

            safe_link(release_path, team_release_path)

    def release_puzzle(self, puzzle):
        if puzzle.is_meta:
            #we need to link in all the files in the round.
            puzzle_path = os.path.join(settings.PUZZLE_PATH, puzzle.round_path)
            team_puzzle_path = os.path.join(settings.TEAM_PATH, self.id, puzzle.round_path)
            for filename in os.listdir(puzzle_path):
                puzzle_filename = os.path.join(puzzle_path, filename)

                #... but not the directories, except for
                #investigators_report, which is the meta for critic rounds
                if os.path.isdir(puzzle_filename) and not filename == "investigators_report":
                    continue
                team_puzzle_filename = os.path.join(team_puzzle_path, filename)
                safe_link(puzzle_filename, team_puzzle_filename)

        else:
            puzzle_path = os.path.join(settings.PUZZLE_PATH, puzzle.path)
            team_puzzle_path = os.path.join(settings.TEAM_PATH, self.id, puzzle.path)
            safe_link(puzzle_path, team_puzzle_path)

    def unrelease_puzzle(self, puzzle):
        team_puzzle_path = os.path.join(settings.TEAM_PATH, self.id, puzzle.path)
        safe_unlink(team_puzzle_path)

    @property
    def team_path(self):
        return os.path.join(settings.TEAM_PATH, self.id)

    @property
    def next_unlock_time(self):
        """In seconds since Epoch, or -1 if everything is unlocked.
        Depends on at least one batch being unlocked; the first
        batch is unlocked by manage.py start.
        """

        #get the hunt start time
        start_time = get_meta('start_time')
        if start_time is None:
            return None
        start_time = int(start_time)

        #get the current batch
        team_unlock = list(TeamUnlock.objects.filter(team=self).order_by('-batch__batch')[:1])
        if team_unlock:
            batch = team_unlock[0].batch.batch
        else:
            batch = 0

        remaining_batches = list(UnlockBatch.objects.filter(batch__gt=batch).order_by('batch')[:1])

        if not remaining_batches:
            return -1 #everything is unlocked
        next_batch = remaining_batches[0]
        return start_time + next_batch.base_time - next_batch.minutes_early_per_point * self.score * 60

class Phone(models.Model):
    phone = models.CharField(max_length=20)
    team = models.ForeignKey('Team')

    def __unicode__(self):
        return self.phone

class TeamUnlock(models.Model):
    team = models.ForeignKey('Team')
    batch = models.ForeignKey('UnlockBatch')
    time = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=TeamUnlock)
def post_save_team_unlock(sender, instance=None, **kwargs):
    write_team_info_js(None, instance.team)

@receiver(post_save, sender=Team)
def write_team_info_js(sender, instance=None, **kwargs):
    #if the team has no directory, make one
    safe_mkdirs(instance.team_path)

    if get_meta("start_time"):
        #the hunt is started
        #now create the team info JS file
        try:
            os.mkdir(instance.team_path)
        except OSError:
            #already exists
            pass
        filename = os.path.join(instance.team_path, "points.js")
        tmp_filename = filename + ".tmp"
        js = """
    this.points = %d;
    this.next_unlock_time = %s;
    """ % (instance.score, instance.next_unlock_time)
        f = open(tmp_filename, "w")
        f.write(js)
        f.close()
        os.rename(tmp_filename, filename)

QUEUES = [("Errata", "errata"), ("General", "general"), ("Pick up", "objects"), ("Puzzle-specific request(provide exact puzzle name and exact phrase describing why you are making this request)", "puzzle"), ("Production", "production")]

class Achievement(models.Model):
    title = models.CharField(max_length=100)
    public = models.BooleanField()

    def __unicode__(self):
        return self.title

class TeamAchievement(models.Model):
    team = models.ForeignKey('Team')
    achievement = models.ForeignKey('Achievement')
    time = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(max_length=1000)

class CallRequest(models.Model):
    team = models.ForeignKey('Team')
    phone = models.ForeignKey('Phone')
    time = models.DateTimeField(auto_now_add=True)
    queue = models.CharField(choices=QUEUES, max_length=100)
    handled = models.BooleanField(default=False)
    reason = models.TextField(max_length=1000)
    time_handled = models.DateTimeField()
    owner = models.ForeignKey(User, null=True)

class AnswerRequest(models.Model):
    team = models.ForeignKey('Team')
    phone = models.ForeignKey('Phone')
    time = models.DateTimeField(auto_now_add=True)
    answer = models.CharField(max_length=100)
    answer_normalized = models.CharField(max_length=100)
    puzzle = models.ForeignKey('Puzzle')
    bought_with_event_points = models.BooleanField(default=False)
    backsolve = models.BooleanField(default=False)
    handled = models.BooleanField(default=False)
    correct = models.BooleanField(default=False)
    time_handled = models.DateTimeField(null=True)
    owner = models.ForeignKey(User, null=True)

    class Meta:
        ordering = ['time']

@receiver(post_delete, sender=AnswerRequest)
def post_delete_answer_request(instance=None, **kwargs):
    #deleting an answer request for an answer bought with event points
    #restore the team's event points
    if instance.bought_with_event_points:
        team = instance.team
        team.event_points += team.answer_event_point_cost
        team.save()


@receiver(pre_save, sender=AnswerRequest)
def pre_save_answer_request(instance=None, **kwargs):
    request = instance
    request.correct = request.answer_normalized == request.puzzle.answer_normalized
    if request.handled:
        request.time_handled = datetime.now()

@receiver(pre_save, sender=CallRequest)
def pre_save_call_request(instance=None, **kwargs):
    request = instance
    if request.handled:
        request.time_handled = datetime.now()

@receiver(post_save, sender=TeamAchievement)
def post_save_team_achievement(sender, instance=None, **kwargs):
    achievement_js_path = os.path.join(settings.PUZZLE_PATH, "achievements.js")
    achievements = {}
    for achievement in Achievement.objects.all():
        if not achievement.public: 
            next
        teams = []
        achievements[achievement.title] = teams
        for team_achievement in achievement.teamachievement_set.all():
            teams.append(team_achievement.team.name)

    f = open(achievement_js_path + ".tmp", "w")
    print >>f, json.dumps("achievements(%s);" % achievements)
    os.rename(achievement_js_path + ".tmp", achievement_js_path)
    


@receiver(post_save, sender=AnswerRequest)
def post_save_answer_request(sender, instance=None, **kwargs):
    team = instance.team
    puzzle = instance.puzzle
    if instance.handled == True and instance.correct == True and not Solved.objects.filter(team=team, puzzle = puzzle).count():
        solved = Solved(team = team, puzzle = puzzle,
                        bought_with_event_points = instance.bought_with_event_points)
        solved.save()

        #update team solved js
        solved_path = os.path.join(team.team_path, "solved.js")
        f = open(solved_path + ".tmp", "w")
        solved = dict((canonicalize(solved.puzzle.title), solved.puzzle.id) for solved in Solved.objects.filter(team=team))
        f.write("var puzzle_solved = ")
        f.write(json.dumps(solved))
        f.write(";")
        f.close()
        os.rename(solved_path + ".tmp", solved_path)

        team.nsolved += 1

        #points is actually cubic in number of unlocks, being as sum of
        #squares
        team.score += team.nsolved * team.nsolved
        team.release()
        team.save()

class Puzzle(models.Model):
    #this is a hash of the pony name
    id = models.CharField(max_length=100, primary_key=True)

    #and this is the puzzle's real title
    title = models.CharField(max_length=100)
    round = models.CharField(max_length=100)

    #this only supports one reuse per puzzle, but that would be
    #easy to fix
    matrixed_round = models.CharField(max_length=100, null=True, blank=True)

    answer = models.CharField(max_length=100)
    is_meta = models.BooleanField()
    unlock_batch = models.IntegerField()

    def __unicode__(self):
        return self.title

    @property
    def path(self):
        return os.path.join(canonicalize(self.round), canonicalize(self.title))

    @property
    def round_path(self):
        return os.path.join(canonicalize(self.round))

    @property
    def answer_normalized(self):
        return normalize_answer(self.answer)


@receiver(post_save, sender=Puzzle)
def fixup_puzzle(sender, instance=None, **kwargs):
    """Delete and re-release the puzzle where necessary"""

    if not instance.id:
        return #nothing to do for new puzzles

    old_puzzle = Puzzle.objects.get(id=instance.id)

    already_unlocked_batches = TeamUnlock.objects.filter(batch=instance.unlock_batch)

    for unlock in already_unlocked_batches:
        team = unlock.team
        #the puzzle needs to be pulled and re-released for this team
        team.unrelease_puzzle(old_puzzle)
        team.release_puzzle(instance)

class UnlockBatch(models.Model):
    batch = models.IntegerField()
    base_time = models.IntegerField()
    minutes_early_per_point = models.FloatField()

    class Meta:
        verbose_name_plural = "Unlock Batches"

class Solved(models.Model):
    team = models.ForeignKey('Team')
    puzzle = models.ForeignKey('Puzzle')
    time = models.DateTimeField(auto_now_add=True)
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
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("team", "physical_object")

class EventPointToken(models.Model):
    """An event point token used by a team"""
    team = models.ForeignKey("Team")
    token = models.CharField(max_length=22)

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
