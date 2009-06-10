#!/usr/bin/env python

from ConfigParser import RawConfigParser
from os import listdir, mkdir, symlink
from os.path import abspath, exists, getmtime
from smtplib import SMTP
from time import localtime, strftime, strptime, time
from datetime import datetime
from random import sample
from Cheetah.Template import Template

class Archives(YomikoComponent):

	def default(self, year, month, page=1):
		files = self.get_entry_filenames(self.config["entries_dir"], page)
		files = [(getmtime(self.config["entries_dir"]+"/"+entry), entry) for entry in listdir(self.config["entries_dir"])]
		def archive_filter(pair):
			timestamp = datetime.fromtimestamp(pair[0])
			return timestamp.year == int(year) and timestamp.month == int(month)
		files = filter(archive_filter, files)
		files.sort()
		files.reverse()
		page = int(page)
		files = files[(page-1)*10:page*10]
		if not files:
			raise cherrypy.HTTPError(404)

		entries = []
		for file in files:
			if not file[1].endswith("."+self.config["entry_ext"]):
				continue
			entries.append(self.make_entry_from_file(self.config["entries_dir"]+"/"+file[1]))

		values = {"page" : page, "entries" : entries}
		return self.render("list", values)

	default.exposed = True
