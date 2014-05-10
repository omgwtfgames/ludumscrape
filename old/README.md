ludumscrape
===========

A quick and dirty scraper to extract info from the Ludum Dare web site.

Not likely to be useful for long since it will break if the webiste changes
significantly, but it may be useful for extracting various subsets of entries
(in the example here, all submitted Android games for LD24). 

Please be polite to the Ludum Dare site and DON'T run this script in a
frequent cronjob or anything asshatish like that.

Dependencies:

    pip install requests beautifulsoup4 jinja2

To run:

    python ludumscrape.py

Results are cached in `results.json`. If this file exists, it is read
instead of going back and scraping web pages again. This allows you to
save the scraped info and analyse or reformat it in different ways 
(eg, via the Jinja2 template output included).
