from django.conf import settings
from django.contrib import admin
#from django.contrib.admin import SimpleListFilter
from django.core import urlresolvers
from django.db.models import Q, F
from django import forms
from models import *

class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'location', 'score', 'event_points', 'number_solved')
    list_editable = ('event_points',)

    actions = ['add_point']

    def add_point(self, request, teams):
        teams.update(nsolved=F('nsolved') + 1, score=F('score') + (F('nsolved') + 1) * (F('nsolved') + 1))
        for team in teams:
            team = Team.objects.get(id=team.id) #reload team to get new score/nsolved
            team.release()

    add_point.short_description = "Add one point to team"

    def number_solved(self, team):
        return team.nsolved #just for naming purposes

admin.site.register(Team, TeamAdmin)

class UnlockBatchAdmin(admin.ModelAdmin):
    list_display = ('batch', 'base_time', 'seconds_early_per_point')

admin.site.register(UnlockBatch, UnlockBatchAdmin)

class PuzzleAdmin(admin.ModelAdmin):
    list_display = ('title', 'path', 'round', 'answer', 'is_meta', 'unlock_batch', 'wrong_answers', 'solves')
    list_filter = ('round', 'is_meta', 'unlock_batch')

    def wrong_answers(self, puzzle):
        AnswerRequest.objects.filter(puzzle=puzzle, correct=False).count()

    def solves(self, puzzle):
        AnswerRequest.objects.filter(puzzle=puzzle, correct=True).count()

admin.site.register(Puzzle, PuzzleAdmin)

def team_link(self, areq):
    url = urlresolvers.reverse('admin:solving_team_change', args=(areq.team_id,))
    return '<a href="%s">%s</a> at %s' % (url, areq.team.name, areq.team.phone)
team_link.allow_tags = True

# Aargh, this is only supported in Django 1.4 which is not yet out
# class TakenFilter(SimpleListFilter):
#     title = _('Owner')

#     parameter_name = 'owner'

#     def lookups(self, request, model_admin):
#         return (
#             ('mine_and_no_owner', _('mine and untaken')),
#             ('all', _('all')),
#         )

#     def queryset(self, request, queryset):
#         team = get_team()
#         if self.value() == 'mine_and_no_owner':
#             return queryset.filter(owner=team)
#         if self.value() == 'all':
#             return queryset


class CallRequestAdmin(admin.ModelAdmin):
    list_display = ('team', 'time', 'queue', 'handled', 'time_handled', 'reason', 'owner')
    list_filter = ('queue', 'team', 'handled')
    list_editable = ('handled',)

    fields = ('team_link', 'owner', 'queue', 'handled', 'time_handled', 'reason')
    readonly_fields = ('team_link', 'owner', )
    actions = ('handle', 'claim')

    team_link = team_link

    def claim(self, request, crequests):
        crequests.filter(owner=None).update(owner=request.user)
    claim.short_description = "Claim requests"

    def handle(self, request, crequests):
        for crequest in crequests:
            crequest.handled = True
            crequest.save()
    handle.short_description = "Mark request as handled"

    def queryset(self, request):
        qs = super(CallRequestAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(owner=request.user) | Q(owner=None))

admin.site.register(CallRequest, CallRequestAdmin)

class AnswerRequestAdmin(admin.ModelAdmin):
    list_display = ('team', 'time', 'puzzle_link', 'answer', 'correct', 'handled', 'time_handled', 'backsolve', 'owner')
    list_filter = ('team', 'handled', 'puzzle')
    list_editable = ('handled',)
    fields = ('team_link', 'owner', 'puzzle', 'answer', 'answer_normalized', 'correct', 'time', 'time_handled', 'handled', 'backsolve')
    readonly_fields = ('team_link', 'owner', 'puzzle', 'answer', 'answer_normalized', 'correct', 'time', 'backsolve')
    actions = ('handle', 'claim')

    team_link = team_link

    def puzzle_link(self, areq):
        url = urlresolvers.reverse('admin:solving_puzzle_change', args=(areq.puzzle_id,))
        return '<a href="%s">%s</a>' % (url, areq.puzzle.title)
    puzzle_link.allow_tags = True

    def claim(self, request, crequests):
        crequests.filter(owner=None).update(owner=request.user)
    claim.short_description = "Claim requests"

    def handle(self, request, crequests):
        for crequest in crequests:
            crequest.handled = True
            crequest.save()
    handle.short_description = "Mark request as handled"

    def queryset(self, request):
        qs = super(AnswerRequestAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(owner=request.user) | Q(owner=None))

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
