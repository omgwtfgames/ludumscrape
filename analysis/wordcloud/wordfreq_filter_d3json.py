import sys
import fileinput
try:
    import json
except ImportError:
    import simplejson as json

from nltk.corpus import stopwords

output_top = 100
min_freq = 2
min_wordlength = 3

stops = stopwords.words("english")
stops += ["it's"]

data = []
for line in fileinput.input():
    data += json.loads(line);

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