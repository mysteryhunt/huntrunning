from django import template

register = template.Library()

@register.filter
def lookup(hash, key):
    return hash[key]

@register.filter
def meta_solved(rounds, meta):
    return rounds[meta.round].meta_solved

@register.filter
def puzzles_solved(rounds, meta):
    return rounds[meta.round].puzzles_solved
