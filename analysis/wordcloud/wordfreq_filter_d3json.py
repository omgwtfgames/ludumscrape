import sys
import fileinput
try:
    import json
except ImportError:
    import simplejson as json

from nltk.corpus import stopwords

pos_tag_prefix = "J" # adjective
#pos_tag_prefix = "N" # noun
#pos_tag_prefix = "V" #  verb
#pos_tag_prefix = "R" # adverb
output_top = 100
min_freq = 2
min_wordlength = 3


stops = stopwords.words("english")
stops += ["it's"]

data = []
for line in fileinput.input():
    data += json.loads(line);

if pos_tag_prefix:
    pos_tag_filtered = []
    for word in data:
        if len(word["pos_tag"]) > 0 and word["pos_tag"][0] == pos_tag_prefix:
            pos_tag_filtered.append(word)
    data = pos_tag_filtered

# sort by frequency
data.sort(key=lambda x: x["size"], reverse=True)

filtered = []
for wordfreq in data:
    freq = wordfreq["size"]
    word = wordfreq["text"]
    if freq >= min_freq and len(word.replace("'", "")) >= min_wordlength and word not in stops:
        filtered.append(wordfreq)

filtered = filtered[0:output_top]

print "var word_freqs = " + json.dumps(filtered) + ";"

sys.stderr.write("\n----\n")
sys.stderr.write("Total words, pre-filter: %i\n" % len(data))
sys.stderr.write("Total words, post-filter: %i\n" % len(filtered))
sys.stderr.write("Highest freq (%s): %i\n" % (filtered[:1][0]["text"], filtered[:1][0]["size"]))
