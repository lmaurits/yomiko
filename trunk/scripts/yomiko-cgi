#!/usr/bin/env python

import cherrypy
from flup.server.fcgi import WSGIServer

from yomiko.core import Yomiko

def main():

    root = Yomiko(config = "yomiko.conf")
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
    try:
    	WSGIServer(app).run()
    finally:
    	# This ensures that any left-over threads are stopped as well.
    	cherrypy.engine.stop()

if __name__ == "__main__":

    main()
