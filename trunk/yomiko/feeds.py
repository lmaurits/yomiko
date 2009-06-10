#!/usr/bin/env python

from ConfigParser import RawConfigParser
from os import listdir, mkdir, symlink
from os.path import abspath, exists, getmtime
from smtplib import SMTP
from time import localtime, strftime, strptime, time
from datetime import datetime
from random import sample
from Cheetah.Template import Template

try:
	from feedformatter import Feed
	_CAN_DO_FEEDS = True
except ImportError:
	_CAN_DO_FEEDS = False

class Feeds(YomikoComponent):

	def _get_feed(self):
		if not _CAN_DO_FEEDS:
			raise cherrypy.HTTPError(404)
		
		channel = {}
		channel["title"] = self.config["blog_title"]
		channel["description"] = self.config["blog_desc"]
		channel["webmaster"] = self.config["author_name"]

		items = []
                files = self.get_entry_filenames(self.config["entries_dir"], 1)
                entries = [self.make_entry_from_file(self.config["entries_dir"]+"/"+file) for file in files]
		for entry in entries:
			item = {}
			item["title"] = entry["title"]
			item["link"] = self.config["base_url"] + entry["permalink"]
			item["guid"] = entry["url_title"]
			item["pubDate"] = strptime(entry["timestamp"], "%c")
			item["description"] = entry["entry"]
#			item["description"] = " ".join(entry["entry"].split()[0:100])+"..."
			items.append(item)

		return Feed(channel, items)
	
	def rss1(self):
		feed = self._get_feed()
		cherrypy.response.headers['Content-Type'] = "text/xml"
		return feed.format_rss1_nofile(validate=False, pretty=True)
	rss1.exposed = True

	def rss2(self):
		feed = self._get_feed()
		cherrypy.response.headers['Content-Type'] = "text/xml"
		return feed.format_rss2_nofile(validate=False, pretty=True)
	rss2.exposed = True

	def atom(self):
		feed = self._get_feed()
		cherrypy.response.headers['Content-Type'] = "text/xml"
		return feed.format_rss2_nofile(validate=False, pretty=True)
	atom.exposed = True
