from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hashlib import md5
from hunt.solving.models import Team

import Crypto.Cipher.AES as aes
import os
import qrencode
import uuid
import base64


#these are the the numbers of each denomination that Codex's event
#coordinator computed that we would need given ~50 teams * ~(50-100)
#points per event * 6 events.  I don't know how accurate they are,
#since there were a couple of bugs which caused the tokens to be full
#of fail.  I believe that I cleaned that up, but someone who understands
#security well should check it over to be sure.

denominations = [(5, 100), (10, 145), (20, 290), (50, 180), (55, 2), (60, 2), (65, 2), (70, 2), (75, 2), (80, 1)]

code_dir = "/tmp/codes"

ROWS_PER_PAGE=5

class Command(BaseCommand):
    help = """Generates a set of event point tokens in various
    denominations."""

    def handle(self, *args, **options):

        key = md5("salt" + settings.SECRET_KEY).digest()

        if not os.path.exists(code_dir):
            os.makedirs(code_dir)

        random = open("/dev/urandom")
        codes_html = open(os.path.join(code_dir, "codes.html"), "w")

        encryptor = aes.new(key)

        print >>codes_html,"""<html>
<head>
<style type="text/css">
table {
width:100%;
}
tr {
width:100%;
}
td {
width:50%;
}
</style>
</head>
<body style="margin:0px;padding:0px;">
"""
        j = 0
        for denomination, count in denominations:
            for i in range(count / 2):

                if j % ROWS_PER_PAGE == ROWS_PER_PAGE - 1:
                    break_after = "page-break-after:always;"
                else:
                    break_after=""
                j += 1
                print >>codes_html, "<table style='cell-padding:0px;cell-spacing:0px;padding:0px;margin:0px;spacing:0px;border-collapse:collapse;%s'><tr>" % break_after

                for col in range(2):
                    token_id = "%s-%s" % (denomination, i * 2 + col)

                    data = "%08d%s" % (denomination, random.read(8))
                    token = encryptor.encrypt(data)

                    encoded_token = base64.urlsafe_b64encode(token)[:-2]
                    url = "borbonicusandbodley.com/d/a?t=%s" % encoded_token

                    enc = qrencode.Encoder()
                    im = enc.encode(url, { 'width': 100 })
                    im.save(os.path.join(code_dir, '%s.png' % token_id))
                    print >>codes_html,"""
<td style="border:thin dashed black;text-align:center;">
%s bupkis<br/>
<img src="%s.png"><br/>
%s<br/>
</td>
""" % (denomination, token_id, url.replace("?","?<br/>"))
                
                print >>codes_html, "</tr></table>"
        print >>codes_html,"</body></html>"
