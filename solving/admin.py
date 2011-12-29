from django.conf import settings
from django.contrib import admin
from django.core import urlresolvers
from django import forms

from models import *

class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'location', 'score', 'unlocked')
    

admin.site.register(Team, TeamAdmin)

class UnlockBatchAdmin(admin.ModelAdmin):
    list_display = ('batch', 'points_required')

admin.site.register(UnlockBatch, UnlockBatchAdmin)

class PuzzleAdmin(admin.ModelAdmin):
    list_display = ('title', 'path', 'round', 'answer', 'is_meta', 'unlock_batch')

admin.site.register(Puzzle, PuzzleAdmin)

class CallRequestAdmin(admin.ModelAdmin):
     list_display = ('team', 'time', 'queue', 'handled', 'reason')
     list_filter = ('queue', 'team', 'handled')
     list_editable = ('handled',)
     actions = ('handle',)

     def handle(self, request, crequests):
         for crequest in crequests:
             crequest.handled = True
             crequest.save()
     handle.short_description = "Mark request as handled"

admin.site.register(CallRequest, CallRequestAdmin)

class AnswerRequestAdmin(admin.ModelAdmin):
     list_display = ('team', 'time', 'puzzle_link', 'answer', 'correct', 'handled')
     list_filter = ('team', 'handled', 'puzzle')
     list_editable = ('handled',)
     readonly_fields = ('team', 'puzzle', 'answer', 'answer_normalized', 'correct', 'time')
     actions = ('handle',)

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
