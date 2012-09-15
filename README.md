ludumscrape
===========

A quick and dirty scraper to extract info from the Ludum Dare web site.

Not likely to be useful for long since it will break if the webiste changes
significantly, but it may be useful for extracting various subsets of entries
(in the example here, all submitted Android games for LD24). 

Please be polite to the Ludum Dare site and DON'T run this script in a
frequent cronjob or anything asshatish like that.

Dependencies:

  pip install requests
  pip install beautifulsoup4
  pip install jinja2
