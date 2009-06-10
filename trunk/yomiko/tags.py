#!/usr/bin/env python

from os.path import exists

from yomiko.core import YomikoComponent

class Tags(YomikoComponent):

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
