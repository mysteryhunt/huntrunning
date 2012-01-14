from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hashlib import md5
from hunt.solving.models import Team

import Crypto.Cipher.AES as aes
import os
import qrencode
import uuid
import base64

denominations = [(5, 100), (10, 145), (20, 290), (50, 181), (55, 2), (60, 2), (65, 2), (70, 2), (75, 2), (80, 1)]

code_dir = "/tmp/codes"

ROWS_PER_PAGE=5

class Command(BaseCommand):
    help = """Generates a set of event point tokens in various
    denominations."""

    def handle(self, *args, **options):

        if not os.path.exists(code_dir):
            os.makedirs(code_dir)

        random = open("/dev/random")
        codes_html = open(os.path.join(code_dir, "codes.html"), "w")

        encryptor = aes.new(md5("salt" + settings.SECRET_KEY).digest())

        print >>codes_html,"""<html>
<head>
<style>
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
                    token_id = "%s-%s" % (denomination, i)

                    data = "%04d%s" % (denomination, random.read(12))
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
