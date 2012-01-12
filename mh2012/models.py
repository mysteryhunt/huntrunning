from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from hunt.common import safe_link, safe_unlink, safe_mkdirs
from hunt.solving.models import Team, Puzzle, Solved

from datetime import timedelta

#45 minutes
PRODUCTION_POINT_DELAY = 45 * 60

SHOWS = [('A Circus Line', 'A Circus Line'),
         ('Okla-Holmes-a!', 'Okla-Holmes-a!'),
         ('Into the Woodstock', 'Into the Woodstock'),
         ('Mayan Fair Lady', 'Mayan Fair Lady'),
         ('Phantom of the Operator', 'Phantom of the Operator'),
         ('Ogre of La Mancha', 'Ogre of La Mancha'),
         ("Let's Put on a Hit!", "Let's Put on a Hit!"),
         ('Password Reminder', 'Password Reminder'),
         ]


class ShowProduced(models.Model):
    class Meta:
        verbose_name_plural = "Shows Produced"

    team = models.ForeignKey(Team)
    round = models.CharField(choices = SHOWS, max_length=100)
    release_at = models.DateTimeField()

    #this is the friday afternoon case: we want to give them the points
    #but not the puzzle
    do_not_release_puzzle_yet = models.BooleanField()

    #these are system fields, controlled by the production
    #release script
    point_released = models.BooleanField()
    puzzle_released = models.BooleanField()

    unique_together=(('team', 'round'),)

    @property
    def puzzle(self):
        return Puzzle.objects.get(round="Letters From Max and Leo", puzzle=self.round)

    def __unicode__(self):
        return "%s produced %s" % (self.team, self.round)

@receiver(pre_save, sender=ShowProduced)
def pre_save_production(sender, instance, **kwargs):
    #compute release time from delay + later of the meta solves

    if instance.round == "Password Reminder" or instance.round == "Let's Put on a Hit!":
        instance.release_at = last_solve_time
    else:
        other_round_id = corresponding_metas[instance.round]
        solve_time = Solved.objects.get(team=instance.team, puzzle__is_meta=True, puzzle__round=instance.round).time

        other_solve_time = Solved.objects.get(team=instance.team, puzzle__is_meta=True, puzzle__round=other_round_id).time

        last_solve_time = max(solve_time, other_solve_time)
        instance.release_at = last_solve_time + timedelta(0, PRODUCTION_POINT_DELAY)



#which show metas correspond to which critic metas
corresponding_metas = {
    'A Circus Line' : 'Betsy Johnson',
    'Betsy Johnson' : 'A Circus Line',
    'Okla-Holmes-a!' : 'Charles Lutwidge Dodgson',
    'Charles Lutwidge Dodgson' : 'Okla-Holmes-a!',
    'Into the Woodstock' : 'William S. Bergman',
    'William S. Bergman' : 'Into the Woodstock',
    'Mayan Fair Lady' : 'Ben Bitdiddle',
    'Ben Bitdiddle' : 'Mayan Fair Lady',
    'Phantom of the Operator' : 'Sheila Sunshine', 
    'Sheila Sunshine' : 'Phantom of the Operator',
    'Ogre of La Mancha' : 'Watson 2.0',
    'Watson 2.0' : 'Ogre of La Mancha'
}
