"""

Image Inventory Framework
==========================

This part of code, will be used to push the images to S3.
Using xcloud-stage AWS S3

Contact: Siby Mathew siby.mathew@ruckuswireless.com
Copyright (C) 2017 Ruckus Wireless, Inc.
All Rights Reserved.

"""

from subprocess import call, Popen, PIPE
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import boto
from boto.s3.connection import S3Connection
from boto.s3.connection import Location
from boto.s3.key import Key
from boto.s3 import connect_to_region


class ImagePush(object):
    def __init__(self):
        self.id = os.environ['AWS_ACCESS_KEY_ID']
        self.key = os.environ['AWS_SECRET_ACCESS_KEY']
        self.bucket = 'vriot'
        self.base_url = "https://s3-us-west-2.amazonaws.com/"

    def upload(self, branch, version, iFiles=[]):
        n_list = []
        try:
            s3_conn = boto.connect_s3(aws_access_key_id=self.id, aws_secret_access_key=self.key)
            get_bucket = s3_conn.get_bucket(self.bucket)
        except:
            return "Connection Failed or Default bucket is absent."
        else:
            base_path = "{}/{}".format(branch, version)

            for iFile in iFiles:
                abs_path = "{}/{}".format(base_path, iFile)
                file = Key(get_bucket)
                file.key = abs_path
                file.set_contents_from_filename(iFile)
                file.set_acl('public-read')
                n_list.append(self.base_url + self.bucket + "/" + abs_path)

        self.notification(version, n_list)

    def notification(self, version, n_list):
        TO = os.environ['EMAIL_LIST_TO'].split(',')
        FROM = os.environ['EMAIL_LIST_FROM']
        USER = os.environ['GMAIL_NOTIF_USER']
        PASSWORD = os.environ['GMAIL_NOTIF_PASSWORD']
        if not TO or not FROM:
            return False

        SUBJECT = "Build Mail for {}".format(version)
        TEXT = \
        """
        Hi Team,

        Images are available to download at following locations,

        %s

        Thanks,
        VRIOT TEAM
        """ % ("\n\n".join(n_list))

        msg = MIMEMultipart()
        msg['Subject'] = SUBJECT
        msg['From'] = FROM
        msg['To'] = ", ".join(TO)
        text = MIMEText(TEXT, 'plain')
        msg.attach(text)

        server = smtplib.SMTP('smtp.gmail.com')
        server.ehlo()
        server.starttls()
        server.login(USER, PASSWORD)
        server.sendmail(FROM, TO, msg.as_string())
        server.quit()