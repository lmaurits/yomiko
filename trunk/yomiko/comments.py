#!/usr/bin/env python

from os import mkdir
from os.path import exists
from smtplib import SMTP
from time import time

import cherrypy

from yomiko.core import YomikoComponent

class Comments(YomikoComponent):

    def submit(self, title, body, spam_answer, name="Anonymous", email="", url="", submit="", preview=""):
        if spam_answer == cherrypy.session.get('spam_answer'):
            cherrypy.session.clear()
            if not exists(self.config["comments_dir"]+"/"+title):
                mkdir(self.config["comments_dir"]+"/"+title)
            fp = open(self.config["comments_dir"]+"/"+title+"/"+str(int(time()*100))+".cmt", "w")
            fp.write("Name: %s\n" % name)
            fp.write("Email: %s\n" % email)
            fp.write("Url: %s\n" % url)
            fp.write("-----\n")
            fp.write(body)
            fp.close()
            self.send_notice(title, name, email, url, body)

            raise cherrypy.HTTPRedirect(self.config["base_uri"]+"/entry/"+title)
        else:
            cherrypy.session["spam_message"] = "You answered the anti-spam question incorrectly, try again."
            cherrypy.session["comment_name"] = name
            cherrypy.session["comment_email"] = email
            cherrypy.session["comment_url"] = url
            cherrypy.session["comment_body"] = body

            raise cherrypy.HTTPRedirect(self.config["base_uri"]+"/entry/"+title)

    submit.exposed = True

    def send_notice(self, title, name, email, url, body):

        RECIPIENTS = [self.config["smtp_to_address"]]
        SENDER = self.config["smtp_from_address"]

        msg = "New comment on entry %s by %s (%s, %s):\n\n%s" % (title, name, email, url, body)
        session = SMTP(self.config["smtp_host"])
        session.sendmail(SENDER, RECIPIENTS, msg)
