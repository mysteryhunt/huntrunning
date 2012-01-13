from django.conf import settings 
from hunt.solving.models import Team

import crypt
import os
import random
import string

SALT_VALUES=string.letters + string.digits

def write_htpasswd():
    htpasswd_file = open(settings.HTPASSWD_PATH + ".tmp", "w")
    for team in Team.objects.all():
        # htpasswd stuff
        salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
        htpasswd_file.write("%s:%s\n" % (team.id, crypt.crypt(team.password, salt)))

    salt = random.choice(SALT_VALUES)+random.choice(SALT_VALUES)
    htpasswd_file.write("%s:%s\n" % (settings.ADMIN_NAME, crypt.crypt(settings.ADMIN_PASSWORD, salt)))
    htpasswd_file.close()

    os.rename(settings.HTPASSWD_PATH + ".tmp", settings.HTPASSWD_PATH)
