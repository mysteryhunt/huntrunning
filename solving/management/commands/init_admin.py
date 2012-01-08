from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import Team

import crypt
import os
import random
import string

SALT_VALUES=string.letters + string.digits

class Command(BaseCommand):
    help = """Gives the admin (only) access to the site"""

    def handle(self, *args, **options):
        htpasswd_file = open(settings.HTPASSWD_PATH, "w")

        salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
        htpasswd_file.write("%s:%s\n" % (settings.ADMIN_NAME, crypt.crypt(settings.ADMIN_PASSWORD, salt)))
        htpasswd_file.close()
