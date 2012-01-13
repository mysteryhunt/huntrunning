from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Puzzle

import hashlib
import os
import sys

class Command(BaseCommand):
    help = """Load puzzles from the ponymap into the database
"""

    def handle(self, *args, **options):
        sys.path.append(settings.PONYMAP_PATH)
        import ponymap


        for pony, pony_info in ponymap.PONY_INFO.items():
            pony_id = hashlib.sha224(pony).hexdigest()
            puzzle = list(Puzzle.objects.filter(id=pony_id))
            if puzzle:
                puzzle = puzzle[0]
                puzzle.title = pony_info['title']
                puzzle.answer = pony_info['answer'] or 'NONANSWER'
                puzzle.is_meta = pony_info.get('is_meta', False)
                puzzle.round = pony_info['round']
                puzzle.matrixed_round = pony_info['reused']
                puzzle.unlock_batch = pony_info['batch']
                puzzle.save()
            else:
                puzzle = Puzzle(id=pony_id, title=pony_info['title'],
                                answer=pony_info['answer'] or 'NONANSWER',
                                round=pony_info['round'],
                                matrixed_round=pony_info['reused'],
                                is_meta=pony_info.get('is_meta', False),
                                unlock_batch = pony_info['batch'])
                puzzle.save()
