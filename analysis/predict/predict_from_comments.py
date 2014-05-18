#!/usr/bin/env python
"""predict_from_comments.py

Usage:
  predict_from_comments.py train [options] INPUTFILES ...
  predict_from_comments.py predict [options] INPUTFILES ...

Arguments:
  INPUTFILE                     Path to a ludumscrape JSON data file

Options:
  -h --help                     Show this message
  --version                     Show the version
  -t, --trained=<filename>      Trained predictor input or output file.
                                [default: trained.pickle.gz]
  --classifier=<type>           Set the classifier type. Valid types are:
                                KNN (k-nearest neighbors),
                                NB (Naive Bayes),
                                SVM (Support Vector Machine)
                                SVR (Support Vector Regression)
                                SLP (Single Layer Averaged Perceptron)
                                [default: KNN]
  --svm-kernel=<type>           Set the SVM kernel used. Valid types are:
                                LINEAR, POLYNOMIAL and RADIAL [default: LINEAR]
  -n <n>, --nfold=<n>           N-fold cross-validation [default: 5]
  -f <n>, --top-features=<n>    Do feature selection via TF/IDF information gain.
                                If zero, include all features
                                (all included words) [default: 200]
  --pos-tags=<tags>             Part-of-speech tag prefixes to
                                include, comma separated J,R,N,V
                                [default: J,R]
  --predict=<feature>           Feature to predict. rating, rating_class,
                                rank_class, percentile_rank,
                                percentile_rank_class. [default: rating_class]
  --rating-category=<category>  Overall, Graphics, Theme, Humor,
                                Audio, Innovation [default: Overall]

Example:
  ./predict_from_comments.py train --pos-tags=J,R --classifier=SVM \
                                   --svm-kernel=LINEAR --top-features 200 \
                                   --rating-category=Graphics \
                                   --predict=rating_class \
                                   ../../results/results_ld*.json

  ./predict_from_comments.py predict --trained=trained.pickle.gz  \
                                     --pos-tags=J,R \
                                     --rating-category=Graphics \
                                     --predict=rating_class \
                                     ../../results/results_ld30.json
"""
__version__ = "0.1"

import sys

from docopt import docopt

#from textblob.taggers import NLTKTagger
from textblob import TextBlob
import pattern
import pattern.vector
from pattern.vector import Document, Model, Classifier, \
                           NB, SVM, KNN, SLP, kfoldcv, count
from pattern.text.en import parsetree

try:
    import json
except ImportError:
    import simplejson as json

options = docopt(__doc__, argv=None, help=True, version=sys.argv[0] + " " + __version__)

trained_filename = options["--trained"]

#classifier_type = "NB"
classifier_type = options["--classifier"]

svm_kernel = getattr(pattern.vector, options["--svm-kernel"])
svm_type = pattern.vector.CLASSIFICATION
if svm_kernel == "SVR":
    svm_type = pattern.vector.REGRESSION
    svm_kernel = "SVM"

#svm_kernel = pattern.vector.LINEAR

#svm_type = pattern.vector.CLASSIFICATION

n_fold = int(options["--nfold"])

select_top_n_features = int(options["--top-features"])
use_feature_selection = (select_top_n_features > 0)

# Define with Position of Speech (POS) tags to include
# in the input vector. All other words are discarded
tag_prefixes = tuple(options["--pos-tags"].split(','))
#tag_prefixes = ()                # don't feature select on POS tags
#tag_prefixes = ("V")             # verb
#tag_prefixes = ("J", "V", "R")    # adjective
#tag_prefixes = ("R")             # adverb
#tag_prefixes = ("N")             # noun

rating_category = options["--rating-category"]
#rating_category = "Overall"
#rating_category = "Graphics"

# What should we try to predict based on the comments ?
# The "_class" options turn it into binary classification
predict = options["--predict"]
#predict = "rating"
#predict = "rating_class"
#predict = "rank_class"
#predict = "percentile_rank"
#predict = "percentile_rank_class"

# Cutoffs for "_class" binary classification
rating_class_cutoff = 4  # 4 means "Scored 4 or more ?"
rank_class_cutoff = 10  # 10 means "In top 10 ?"
percentile_rank_class_cutoff = 10  # 10 means "In top 10th percentile ?"

#nltk_tagger = NLTKTagger()

print sys.argv[0] + " version " + __version__
print "Running with options:"
print options
print


def discard_words_without_tag_of_interest(text, tag_prefixes=tag_prefixes):
    v = parsetree(text, lemmata=True)[0]
    v = [w.lemma for w in v if w.tag.startswith(tag_prefixes)]
    return v


def discard_words_without_tag_of_interest_textblob(text, tag_prefixes=tag_prefixes):
    v = []
    blob = TextBlob(text)  #, pos_tagger=nltk_tagger)
    for word, tag in blob.pos_tags:
        if tag.startswith(tag_prefixes):
            v.append(word)
    return v


data = []
for fn in options["INPUTFILES"]:
    with open(fn) as f:
        for jsonline in f:
            data.append(json.loads(jsonline))

worst_ranking = 0
for entry in data:
    if rating_category not in entry['ratings']:
        continue
    rank = int(entry['ratings'][rating_category][1])
    worst_ranking = max(rank, worst_ranking)

vectors = []
for entry in data:
    url = entry['url']
    author = entry['author']
    # those who didn't rate anything (0% Coolness) get no Overall rating
    if rating_category not in entry['ratings']:
        #sys.stderr.write("Skipping: " + entry['url'] + "\n")
        continue
    rating = int(round(float(entry['ratings'][rating_category][0])))
    rating_class = (rating >= rating_class_cutoff)  # binary classes

    rank = int(entry['ratings'][rating_category][1])
    rank_class = (rank <= rank_class_cutoff)  # top 10 binary classification

    percentile_rank = (float(rank) / float(worst_ranking)) * 100.0
    percentile_rank_class = (percentile_rank <= percentile_rank_class_cutoff)
    #print rank, percentile_rank, percentile_rank_class

    # a value of one of the above is assigned as the property to predict
    output_vector = vars()[predict]

    all_entry_comment_text_filtered = ""
    entry_comments = []
    for comment in entry['comments']:
        text = comment[3]
        if tag_prefixes:
            text = " ".join(discard_words_without_tag_of_interest_textblob(text))
            #text = " ".join(discard_words_without_tag_of_interest(text))

        entry_comments.append(text)

        # document = individual comments
        #vectors.append(Document(text,
        #                        type=output_vector,
        #                        stopwords=True))

    all_entry_comment_text_filtered = " ".join(entry_comments)

    #print all_entry_comment_text_filtered
    # document = all comments for one game entry (seems to work better)
    vectors.append(Document(all_entry_comment_text_filtered,
                            name="%s\t%s" % (author, url),
                            type=output_vector,
                            stopwords=True))

if use_feature_selection:
    vectors = Model(documents=vectors, weight=pattern.vector.TFIDF)
    vectors = vectors.filter(features=vectors.feature_selection(top=select_top_n_features))
    #print vectors.vectors

if options["train"]:
    if classifier_type == "SVM":
        classifier = SVM(train=vectors,
                         type=svm_type,
                         kernel=svm_kernel)
    else:
        classifier = getattr(pattern.vector, classifier_type)(train=vectors)

    print "Classes: " + repr(classifier.classes)

    #performance = kfoldcv(NB, vectors, folds=n_fold)
    performance = kfoldcv(type(classifier), vectors, folds=n_fold)
    print "Accuracy: %.3f\n" \
          "Precision: %.3f\n" \
          "Recall: %.3f\n" \
          "F1: %.3f\n" \
          "Stddev:%.3f" % performance
    print
    print "Confusion matrx:"
    print classifier.confusion_matrix(vectors).table

    classifier.save(trained_filename)
elif options["predict"]:
    classifier = Classifier.load(trained_filename)
    for v in vectors:
        print "%s\t%s" % (v.name, repr(classifier.classify(v)))

"""
print "\n\n----"
from example_game_comments import example_game_comments

example_game_comments_filtered = " ".join(discard_words_without_tag_of_interest_textblob(example_game_comments))
print "Example comment words: "
print example_game_comments_filtered
print
print "Example prediction: " + repr(classifier.classify(Document(example_game_comments_filtered)))
"""