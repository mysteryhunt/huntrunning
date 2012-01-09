from django.conf import settings
from django.contrib import admin
#from django.contrib.admin import SimpleListFilter
from django.core import urlresolvers
from django import forms
from models import *


class ShowProducedAdmin(admin.ModelAdmin):
    fields = ('team', 'round', 'release_at', 'do_not_release_puzzle_yet', 'point_released', 'puzzle_released')
    readonly_fields = ('release_at', 'point_released', 'puzzle_released')

admin.site.register(ShowProduced, ShowProducedAdmin)
