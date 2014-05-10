#!/usr/bin/env python

# A simple screen scraper to extract info on Ludum Dare entries.
# Customized to discover all the Android entries.
# Saves extracted info as JSON in results.json - delete this file
# if you want to force re-scraping.
#
# Requires BeautifulSoup4, Requests and Jinja2:
#   $ pip install beautifulsoup4 requests Jinja2
#
# License: Simplified BSD License
################################################################################
# Copyright (c) 2012, Andrew Perry (omgwtfgames.com)
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
################################################################################


import sys, signal, time, json, re, random
import requests
from bs4 import BeautifulSoup
sleeptime = (0.5, 10) # min/max sleep between requests
jamtype = "" # "compo" for the 48 compo, "open" for the jam
searchquery = "" # for testing. normally this should and empty string
#start, end = 0, 1608 # 2328
#start, end = 0, 736
start, end = 0, 24
base_url = 'http://www.ludumdare.com/compo/ludum-dare-26/'

_shutdown = False

try:
  fh = open('results.json', 'r')
  bigdict = json.loads(fh.read())
  fh.close()
  sys.stderr.write("Loaded existing results.json\n")
except:
  sys.stderr.write("results.json not found (or parsing error).\nStarting from scratch.\n")
  bigdict = {'entries':[]}

# this catches Ctrl-C and finished the last entry before writing the cache file
def signal_handler(signal, frame):
  sys.stderr.write('Finishing entry, writing results.json and exiting ...\n')
  global _shutdown
  _shutdown = True

signal.signal(signal.SIGINT, signal_handler)

# loop
fh = open('results.json', 'w')
for num in range(start, end, 24):
  url = base_url + '?action=preview&q=%s&etype=%s&start=%i' % (searchquery, jamtype, num)
  page = BeautifulSoup(requests.get(url).text)
  time.sleep(random.random()*sleeptime[1] + sleeptime[0])
  table = page.find(class_='preview')
  links = table.find_all('a')
  for l in links:
    link = base_url + l.get('href')

    # skip any entries we've already saved in results.json previously
    skiplink = False
    for saved in bigdict['entries']:
      if ('url' in saved) and (link == saved['url']):
        print "###! Skipping, already cached: %s\n" % (link)
        skiplink = True
        break
    if skiplink:
      continue

    gamepage = BeautifulSoup(requests.get(link).text)
    time.sleep(random.random()*sleeptime[1] + sleeptime[0])
    linkpara = gamepage.find(class_='links')
    dllinks = linkpara.find_all('a')
    title = gamepage.find(id='compo2').find('h3').text
    try:
      print u"## %s ##" % (title)
    except:
      print u"## %s ##" % (link)
    entry = {}
    entry['url'] = link
    entry['title'] = title
    entry['download_urls'] = {}
    entry['screenshots'] = []
    for screenie in gamepage.find(id='compo2').find('table').find_all('a'):
      entry['screenshots'].append(screenie.get('href'))
    for dl in dllinks:
      platform = dl.text
      dlurl = dl.get('href')
      print platform + ": " + dlurl
      entry['download_urls'][platform] = dlurl
    bigdict['entries'].append(entry)
    print

    if _shutdown:
      break
  if _shutdown:
    break

fh.write(json.dumps(bigdict))
fh.close()


#print
#print "#####################"
#print "## Android entries ##"
#print "#####################"
#print
android_entries = {'entries':[]}
for entry in bigdict['entries']:
  title = entry['title']
  for platform in entry['download_urls']:
    if re.search("Android", platform, flags=re.IGNORECASE):
      try:
        #print u"## %s ##" % (title)
        pass
      except:
        #print u"## %s ##" % (link)
        pass
      #print platform + ": " + entry['download_urls'][platform]
      #print "Screenshots: "
      for s in entry['screenshots']:
        #print s
        pass
      #print
      entry['id'] = entry['url'].split("=")[-1:]
      android_entries['entries'].append(entry)


from jinja2 import Template
template = Template(open("template.jinja2", 'r').read())
fh = open('ludumdroid.html', 'w')
fh.write(template.render(android_entries))
fh.close()
#print template.render(android_entries)



