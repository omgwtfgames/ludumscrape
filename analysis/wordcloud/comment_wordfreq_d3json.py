import sys
import textblob
from textblob import TextBlob

try:
    import json
except ImportError:
    import simplejson as json


def word_freqs(blob):
    from collections import defaultdict
    '''Dictionary of word frequencies in this text.
       We can't use the equivalent function in TextBlob since it's tokenizer can't be overridden.
    '''
    counts = defaultdict(int)
    stripped_words = [textblob.utils.lowerstrip(w) for w in blob.tokens]
    for w in stripped_words:
        counts[w] += 1
    return counts

fn = sys.argv[1]

data = []
with open(fn) as f:
    for jsonline in f:
        data.append(json.loads(jsonline))

# here's how we'd get all the fields for a comment
# for entry in data:
#    for date, name, uid, comment in entry["comments"]:
#        pass

# concatenate all comments into one long string
comment_list = []
for entry in data:
    for comment in entry["comments"]:
        comment_list.append(comment[3])

all_comments = "\n\t\n".join(comment_list)

from nltk.tokenize import RegexpTokenizer
# this tokenizer won't split contractions ("Can't" stays as "Can't")
tokenizer = RegexpTokenizer("[\w']+")

all_comments = TextBlob(all_comments, tokenizer=tokenizer)
word_counts = []
for word, freq in word_freqs(all_comments).iteritems():  # all_comments.word_counts.iteritems():
    try:
        pos_tag = TextBlob(word).pos_tags[0][1]
    except IndexError:
        pos_tag = ""
    word_counts.append({"text": word, "size": freq, "pos_tag": pos_tag})

# sort by frequency
word_counts.sort(key=lambda x: x["size"], reverse=True)

print json.dumps(word_counts)
