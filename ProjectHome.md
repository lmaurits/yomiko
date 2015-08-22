# Yomiko #

A lightweight, filesystem-based WSGI blogging application built on CherryPy and Cheetah.

## Features ##

  * Update your blog from the command line using your favourite text editor!
  * No need to install and configure a whole RDBMS just for a simple blog!
  * Runs on CherryPy's built in web server _or_ in conjunction with Apache, lighttpd etc. as CGI, FastCGI or SCGI.
  * Comment support (with basic spam protection)
  * Tag support
  * Feed support in RSS 1.0, RSS 2.0 and Atom 1.0 formats (provided by [feedformatter](http://code.google.com/p/feedformatter))

## Requirements ##

  * [CherryPy](http://www.cherrypy.org) (a great Python HTTP framework)
  * [Cheetah](http://www.cheetahtemplate.org) (a simple Python templating system)
  * [flup](http://trac.saddi.com/flup/) (only if running with Apache, lighttpd, etc.)
  * [feedformatter](http://code.google.com/p/feedformatter) (only if feed support desired)

## Formerly known as CherryBlosxom! ##

Yomiko was formerly known as CherryBlosxom (Cherry due to the dependency on CherryPy and Blosxom due to it being inspired by the [lightweight Perl blogging app](http://www.blosxom.com) of that name) and hosted [here](http://www.luke.maurits.id.au/software/cherryblosxom).  At the time I thought the name CherryBlosxom was so unique it never occurred to me to check if it had already been used.  It turns out that someone wrote a Ruby port of Blosxom years ago and called it Cherry Blosxom!  Even though that project appears to be dead, when I migrated my CherryBlosxom to Google code I decided it would be best to rename it.