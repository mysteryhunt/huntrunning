from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team, Phone

import csv

class Command(BaseCommand):
    help = """Load teams from a CSV file
"""

    def handle(self, *args, **options):
        teamcsv = args[0]
        f = csv.reader(open(teamcsv))
        for line in f:
            if len(line) < 19:
                line = line + [""] * (19-len(line))
            _, name, email, _, username, password, _, _, _, _, _, _, _, _, _, _, _, phones,location = line[:19]
            if username == "Username":
                #header
                continue
            team = Team(id=username,name=name,password=password,email=email,location=location)
            team.save()
            team.phone_set.all().delete()
            for phone in phones.split("\n"):
                if not phone:
                    continue
                Phone(team=team,phone=phone).save()
