#!/usr/pkg/bin/python2.4

from ConfigParser import RawConfigParser
from os import listdir, mkdir, symlink
from os.path import abspath, exists, getmtime
from smtplib import SMTP
from time import localtime, strftime, strptime, time
from datetime import datetime
from random import sample
from Cheetah.Template import Template

import cherrypy
from flup.server.fcgi import WSGIServer

try:
	from feedformatter import Feed
	_CAN_DO_FEEDS = True
except ImportError:
	_CAN_DO_FEEDS = False

class CherryBlosxomComponent:

	def __init__(self, config = None, root = None):
		if root:
			self.config = root.config
		if config:
			configparser = RawConfigParser()
			configparser.read(config)
			config = dict(configparser.items("main"))

			defaults = (	("blog title", "Another Cherryblosxom Blog"),
					("template", "default" ))

			for (key, value) in defaults:
				if key not in config:
					config[key] = value
	
			self.config = config

	def render(self, template, values):
		template = Template(file = "templates/%s/%s.tmp" % (self.config["template"], template), searchList = [values])
		values["cherryblosxom_content"] = str(template)

		values["blog_title"] = self.config["blog_title"]
		values["home_link"] = self.config["base_uri"]
		values["rss_link"] = self.config["base_uri"] + "/feeds/rss"
		values["rss2_link"] = self.config["base_uri"] + "/feeds/rss2"
		values["atom_link"] = self.config["base_uri"] + "/feeds/atom"

		files = listdir(self.config["entries_dir"])
		archive_links = []
		seen = []
		for file in files:
			timestamp = localtime(getmtime(self.config["entries_dir"]+"/"+file))
			pair = (strftime("%Y", timestamp), strftime("%B", timestamp))
			if pair not in seen:
				seen.append(pair)
				archive_links.append((timestamp, strftime("%B %Y", timestamp), strftime(self.config["base_uri"]+"/archives/%Y/%m", timestamp)))
		archive_links.sort()
		archive_links.reverse()
		archive_links = [(text, link) for (pair, text, link) in archive_links]
		values["archive_links"] = archive_links
				
		tags = [(len(listdir(self.config["tags_dir"]+"/"+tag)), tag) for tag in listdir(self.config["tags_dir"])]
		tags.sort()
		tags.reverse()
		tags = [(tag, self.config["base_uri"]+"/tags/"+tag, count) for (count, tag) in tags]
		values["tags"] = tags
		template = Template(file = "templates/%s/layout.tmp" % self.config["template"], searchList = [values])
		return str(template)

	def get_entry_filenames(self, directory, page=1):
		files = [(getmtime(directory+"/"+file), file) for file in listdir(directory)]
		files.sort()
		files.reverse()
		files = [file for (timestamp, file) in files]
		files = filter(lambda(f): f.endswith("."+self.config["entry_ext"]), files)	
		page = int(page)
		return files[(page-1)*10:page*10]

	def make_entry_from_file(self, filename):
		fp = open(filename, "r")
		entry = {}
		entry["title"] = fp.readline().strip()
		entry["url_title"] = filename.rsplit("/",1)[-1][0:-4]
		entry["timestamp"] = strftime("%c", localtime(getmtime(filename)))
		line = fp.readline()
		if line.startswith("#tags"):
			entry["tags"] = line.strip()[6:].split(",")
			entry["tags"] = [tag.strip() for tag in entry["tags"]]
			entry["tags"] = [(tag, self.config["base_uri"]+"/tags/"+tag) for tag in entry["tags"]]
			entry["entry"] = ""
		else:
			entry["tags"] = [("untagged", self.config["base_uri"]+"/tags/untagged")]
			entry["entry"] = line
		entry["entry"] += fp.read().strip()
		entry["permalink"] = self.config["base_uri"]+"/entry/"+entry["url_title"]
		if exists(self.config["comments_dir"]+"/"+entry["url_title"]):
			entry["comment_count"] = len(listdir(self.config["comments_dir"]+"/"+entry["url_title"]))
		else:
			entry["comment_count"] = 0
		fp.close()

		self.handle_tags(filename, [tag[0] for tag in entry["tags"]])

		return entry

	def handle_tags(self, filename, tags):
		basename = filename.rsplit("/",1)[-1]
		for tag in tags:
			if not exists(self.config["tags_dir"]+"/"+tag):
				mkdir(self.config["tags_dir"]+"/"+tag)
			if not exists(self.config["tags_dir"]+"/"+tag+"/"+basename):
				symlink(abspath(self.config["entries_dir"]+"/"+basename), self.config["tags_dir"]+"/"+tag+"/"+basename)

class CherryBlosxom(CherryBlosxomComponent):

	def index(self, page=1):
		page = int(page)
		files = self.get_entry_filenames(self.config["entries_dir"], page)
		if not files:
			raise cherrypy.HTTPError(404)
		entries = [self.make_entry_from_file(self.config["entries_dir"]+"/"+file) for file in files]
		values = {"page" : page, "entries" : entries}
		if page == 2:
			values["earlier_link"] = self.config["base_uri"]+"/"
		elif page > 1:
			values["earlier_link"] = self.config["base_uri"]+"/?page="+str(page-1)
		if len(entries) == 10:
			values["later_link"] = self.config["base_uri"]+"/?page="+str(page+1)
		return self.render("list", values)

	index.exposed = True

	def stupid_test(self):

		return abspath(self.config["entries_dir"]+"/prime_time.txt")

	stupid_test.exposed = True

class Entry(CherryBlosxomComponent):

	def default(self, title):
		url_title = title
		if exists(self.config["entries_dir"]+"/"+title+"."+self.config["entry_ext"]):
			# Get entry and comments
			values = self.make_entry_from_file(self.config["entries_dir"]+"/"+title+"."+self.config["entry_ext"])
			values["comments"] = self.get_comments(url_title)

			# Pick random anti-spam question
			choices = ( ("What is the opposite of hot?", "cold"),
						("What is the opposite of cold?", "hot"),
						("What is the opposite of up?", "down"),
						("What is the opposite of down?", "up"),
						("What is the opposite of left?", "right"),
						("What is the opposite of top?", "bottom"),
						("What is the opposite of bottom?", "top"),
						("What is the opposite of in?", "out"))
			#What is the opposite of out?", "in" ), ( "What is the opposite of on?", "off" ), ( "What is the opposite of off?", "on" )]s-mpl0mpl4
			question, answer = sample(choices, 1)[0]
			cherrypy.session["spam_answer"] = answer

			values["spam_question"] = question
			values["comment_link"] = self.config["base_uri"]+"/comments/submit"
			values["spam_message"] = cherrypy.session.get("spam_message")
			values["comment_name"] = cherrypy.session.get("comment_name")
			values["comment_email"] = cherrypy.session.get("comment_email")
			values["comment_url"] = cherrypy.session.get("comment_url")
			values["comment_body"] = cherrypy.session.get("comment_body")

			return self.render("entry", values)	
		else:
			raise cherrypy.HTTPError(404)

	def get_comments(self, title):
		if exists(self.config["comments_dir"]+"/"+title):
			comment_files = listdir(self.config["comments_dir"]+"/"+title)
			comment_files.sort()
			return [self.get_comment_from_file(self.config["comments_dir"]+"/"+title+"/"+comment_file) for comment_file in comment_files]
		else:
			return []

	def get_comment_from_file(self, filename):
			comment = {}
			comment["timestamp"] = strftime("%c", localtime(float(filename.rsplit("/",1)[1][0:-4])/100))
			fp = open(filename, "r")
			while True:
				line = fp.readline().strip()
				if line == "-----":
					break
				else:
					key, value = line.split(":",1)
					comment[key.strip().lower()] = value.strip()
			comment["comment"] = fp.read()
			fp.close()
			return comment

	default.exposed = True

class Archives(CherryBlosxomComponent):

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

class Tags(CherryBlosxomComponent):

	def default(self, tag, page=1):
		if exists(self.config["tags_dir"]+"/"+tag):
			files = self.get_entry_filenames(self.config["tags_dir"]+"/"+tag, page)
			if not files:
				raise cherrypy.HTTPError(404)
			entries = [self.make_entry_from_file(self.config["tags_dir"]+"/"+tag+"/"+file) for file in files]
			values = {"page" : page, "entries" : entries}
			return self.render("list", values)
		else:
			raise cherrypy.HTTPError(404)

	default.exposed = True

class Comments(CherryBlosxomComponent):

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

class Feeds(CherryBlosxomComponent):

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

root = CherryBlosxom(config = "cherryblosxom.conf")
root.entry = Entry(root = root)
root.archives = Archives(root = root)
root.tags = Tags(root = root)
root.comments = Comments(root = root)
root.feeds = Feeds(root = root)

def error404(status, message, traceback, version):
	values = {}
	return root.render("error404", values)

app = cherrypy.tree.mount(root, script_name=root.config["base_uri"], config="cherrypy.conf")
cherrypy.config.update({'error_page.404': error404})

cherrypy.engine.start(blocking=False)
#cherrypy.engine.start()
try:
	WSGIServer(app).run()
finally:
	# This ensures that any left-over threads are stopped as well.
	cherrypy.engine.stop()
