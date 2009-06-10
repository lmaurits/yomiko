#!/usr/bin/env python

from ConfigParser import RawConfigParser
from os import listdir, mkdir, symlink
from os.path import abspath, exists, getmtime
from time import localtime, strftime

import cherrypy
from Cheetah.Template import Template

class YomikoComponent:

    def __init__(self, config = None, root = None):
        if root:
            self.config = root.config
        if config:
            configparser = RawConfigParser()
            configparser.read(config)
            config = dict(configparser.items("main"))

            defaults = (    ("blog title", "Another Cherryblosxom Blog"),
                    ("template", "default" ))

            for (key, value) in defaults:
                if key not in config:
                    config[key] = value
    
            self.config = config

    def render(self, template, values):
        template = Template(file = "templates/%s/%s.tmp" % (self.config["template"], template), searchList = [values])
        values["yomiko_content"] = str(template)

        values["blog_title"] = self.config["blog_title"]
        values["home_link"] = self.config["base_uri"]
        values["rss_link"] = self.config["base_uri"] + "/feeds/rss"
        values["rss2_link"] = self.config["base_uri"] + "/feeds/rss2"
        values["atom_link"] = self.config["base_uri"] + "/feeds/atom"

        files = listdir(self.config["entries_dir"])
        archive_links = []
        seen = []
        for file_ in files:
            timestamp = localtime(getmtime(self.config["entries_dir"]+"/"+file_))
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
        files = [(getmtime(directory+"/"+file_), file_) for file_ in listdir(directory)]
        files.sort()
        files.reverse()
        files = [file_ for (timestamp, file_) in files]
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

class Yomiko(YomikoComponent):

    def index(self, page=1):
        page = int(page)
        files = self.get_entry_filenames(self.config["entries_dir"], page)
        if not files:
            raise cherrypy.HTTPError(404)
        entries = [self.make_entry_from_file(self.config["entries_dir"]+"/"+file_) for file_ in files]
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
