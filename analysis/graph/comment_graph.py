#!/usr/bin/env python
"""
Output the graph structure of comments in a Ludum Dare competition.

(NOTE: Only suitable for LD18 onwards, since prior to that the website does
not provide the UID of the comment author, just a Wordpress "display name".
These display names are mutable, so they aren't a strong identifier for a user.
It should be possible to map many display names to UID based on later LDs,
but we aren't bothering to do that right now).
"""
from __future__ import print_function

import sys

try:
    import json
except ImportError:
    import simplejson as json

def output_gdf(nodes, links):
    """
    Output a directed graph of comments in GDF (GUESS) format.
    Authors (UIDs) are nodes, edges are comments. Edges point from the
    author of a comment to the UID they are commenting on.
    http://guess.wikispot.org/The_GUESS_.gdf_format
    """
    print("nodedef>name VARCHAR,label VARCHAR")
    for n in nodes:
        label = n["label"].replace(',', '').encode('utf-8')
        print("{0},{1}".format(str(n["name"]), label))
    print("edgedef>node1 VARCHAR,node2 VARCHAR")
    for e in links:
        print("{0},{1}".format(e["source"], e["target"]))

def output_d3(nodes, links):
    """
    Output the graph in a format suitable for use with D3.js, like:
    http://bl.ocks.org/mbostock/4062045
    """
    out = {"nodes": nodes, "links": links}
    print(json.dumps(out))

if __name__ == "__main__":
    fn = sys.argv[1]

    data = []
    with open(fn) as f:
        for jsonline in f:
            data.append(json.loads(jsonline))
    nodes = []
    links = []
    for entry in data:
        uid = entry['url'].split("&uid=")[1].strip()
        nodes.append({"label": entry['author'], "name": uid, "group": 1})
        for comment in entry['comments']:
            commenter = comment[2]
            links.append({"target": uid, "source": commenter, "value": 1})

    output_gdf(nodes, links)

