from django.conf import settings
from django.contrib import admin
from django.core import urlresolvers
from django import forms

from models import *

class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'location', 'score', 'event_points', 'nsolved')
    list_editable = ('event_points',)
    

admin.site.register(Team, TeamAdmin)

class UnlockBatchAdmin(admin.ModelAdmin):
    list_display = ('batch', 'base_time', 'seconds_early_per_point')

admin.site.register(UnlockBatch, UnlockBatchAdmin)

class PuzzleAdmin(admin.ModelAdmin):
    list_display = ('title', 'path', 'round', 'answer', 'is_meta', 'unlock_batch', 'wrong_answers', 'solves')

    def wrong_answers(self, puzzle):
        AnswerRequest.objects.filter(puzzle=puzzle, correct=False).count()

    def solves(self, puzzle):
        AnswerRequest.objects.filter(puzzle=puzzle, correct=True).count()

admin.site.register(Puzzle, PuzzleAdmin)

def team_link(self, areq):
    url = urlresolvers.reverse('admin:solving_team_change', args=(areq.team_id,))
    return '<a href="%s">%s</a> at %s' % (url, areq.team.name, areq.team.phone)
team_link.allow_tags = True


class CallRequestAdmin(admin.ModelAdmin):
     list_display = ('team', 'time', 'queue', 'handled', 'time_handled', 'reason')
     list_filter = ('queue', 'team', 'handled')
     list_editable = ('handled',)

     fields = ('team_link', 'queue', 'handled', 'time_handled', 'reason')
     readonly_fields = ('team_link',)
     actions = ('handle',)

     team_link = team_link

     def handle(self, request, crequests):
         for crequest in crequests:
             crequest.handled = True
             crequest.save()
     handle.short_description = "Mark request as handled"

admin.site.register(CallRequest, CallRequestAdmin)

class AnswerRequestAdmin(admin.ModelAdmin):
     list_display = ('team', 'time', 'puzzle_link', 'answer', 'correct', 'handled', 'time_handled', 'backsolve')
     list_filter = ('team', 'handled', 'puzzle')
     list_editable = ('handled',)
     fields = ('team_link', 'puzzle', 'answer', 'answer_normalized', 'correct', 'time', 'time_handled', 'handled', 'backsolve')
     readonly_fields = ('team_link', 'puzzle', 'answer', 'answer_normalized', 'correct', 'time', 'backsolve')
     actions = ('handle',)

     team_link = team_link

     def puzzle_link(self, areq):
         url = urlresolvers.reverse('admin:solving_puzzle_change', args=(areq.puzzle_id,))
         return '<a href="%s">%s</a>' % (url, areq.puzzle.title)
     puzzle_link.allow_tags = True

     def handle(self, request, crequests):
         for crequest in crequests:
             crequest.handled = True
             crequest.save()
     handle.short_description = "Mark request as handled"

admin.site.register(AnswerRequest, AnswerRequestAdmin)

class PhysicalObjectAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(PhysicalObject, PhysicalObjectAdmin)


class PhysicalObjectDistributionAdmin(admin.ModelAdmin):
    list_display = ('physical_object', 'team', 'time')
    list_filter = ('physical_object', 'team')

admin.site.register(PhysicalObjectDistribution, PhysicalObjectDistributionAdmin)


class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title',)

admin.site.register(Achievement, AchievementAdmin)


class TeamAchievementAdmin(admin.ModelAdmin):
    list_display = ('achievement', 'team', 'time')
    list_filter = ('achievement', 'team')

admin.site.register(TeamAchievement, TeamAchievementAdmin)


# this would be nice to have
# class VisitRequestAdminForm(forms.ModelForm):
#     class Meta:
#         model = VisitRequest

#     visit_time = forms....(TODO:datetime)
    
# class VisitRequestAdmin(admin.ModelAdmin):
#     list_display = ('team', 'request_time', 'reason', 'visit_time')
#     list_filter = ('team',)
#    form = VisitRequestAdminForm

# admin.site.register(VisitRequest, VisitRequestAdmin)
