from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team

import csv

class Command(BaseCommand):
    help = """Load teams from a CSV file
"""

    def handle(self, *args, **options):
        teamcsv = args[0]
        f = csv.reader(open(teamcsv))
        for line in f:
            _, name, email, _, username, password, _, _, _, _, phone = line[:11]
            if username == "Username":
                #header
                continue
            Team(id=username,name=name,password=password,email=email,phone=phone).save()
