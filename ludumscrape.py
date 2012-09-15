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


import sys, time, json, re
import requests
from bs4 import BeautifulSoup
sleeptime = 2.0
start, end = 0, 1400
#start, end = 72, 96
base_url = 'http://www.ludumdare.com/compo/ludum-dare-24/'

try:
  fh = open('results.json', 'r')
  bigdict = json.loads(fh.read())
  fh.close()
except:
  bigdict = {'entries':[]}
  # loop
  for num in range(start, end, 24):
    url = 'http://www.ludumdare.com/compo/ludum-dare-24/?action=preview&q=&etype=&start=%i' % (num)
    page = BeautifulSoup(requests.get(url).text)
    time.sleep(sleeptime)
    table = page.find(class_='preview')
    links = table.find_all('a')
    for l in links:
      link = base_url + l.get('href')
      gamepage = BeautifulSoup(requests.get(link).text)
      time.sleep(sleeptime)
      linkpara = gamepage.find(class_='links')
      dllinks = linkpara.find_all('a')
      title = gamepage.find(id='compo2').find('h3').text
      try:
        sys.stderr.write(u"## %s ##\n" % (title))
      except:
        sys.stderr.write(u"## %s ##\n" % (link))
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
        sys.stderr.write(platform + ": " + dlurl + "\n")
        entry['download_urls'][platform] = dlurl
      bigdict['entries'].append(entry)
      sys.stderr.write("/n")

  fh = open('results.json', 'w')
  fh.write(json.dumps(bigdict))
  fh.close()


#sys.stderr.write("\n")
#sys.stderr.write( "#####################\n")
#sys.stderr.write( "## Android entries ##\n")
#sys.stderr.write( "#####################\n")
#sys.stderr.write("\n")
android_entries = {'entries':[]}
for entry in bigdict['entries']:
  title = entry['title']
  for platform in entry['download_urls']:
    if re.search("Android", platform, flags=re.IGNORECASE):
      try:
        #sys.stderr.write( u"## %s ##\n" % (title))
        pass
      except:
        #sys.stderr.write( u"## %s ##\n" % (link))
        pass
      #sys.stderr.write( platform + ": " + entry['download_urls'][platform]+"\n")
      #sys.stderr.write( "Screenshots: \n")
      for s in entry['screenshots']:
        #sys.stderr.write( s+"\n")
        pass
      #sys.stderr.write("\n")
      entry['id'] = entry['url'].split("=")[-1:]
      android_entries['entries'].append(entry)


from jinja2 import Template
#template = Template(open("template.jinja2", 'r').read())
template = Template(open("template_lite.jinja2", 'r').read())
print template.render(android_entries)



