#!/usr/bin/env python
"""predict_from_comments.py

Usage:
  predict_from_comments.py train [options] INPUTFILES ...
  predict_from_comments.py predict [options] INPUTFILES ...

Arguments:
  INPUTFILE                     Path to a ludumscrape JSON data file

Options:
  -h --help                       Show this message
  --version                       Show the version
  -t <fn>, --trained=<filename>   Trained predictor input or output file.
                                  [default: trained.pickle.gz]
  --classifier=<type>             Set the classifier type. Valid types are:
                                  KNN (k-nearest neighbors),
                                  NB (Naive Bayes),
                                  SVM (Support Vector Machine)
                                  SVR (Support Vector Regression)
                                  SLP (Single Layer Averaged Perceptron)
                                  [default: KNN]
  --svm-kernel=<type>             Set the SVM kernel used. Valid types are:
                                  LINEAR, POLYNOMIAL and RADIAL [default: LINEAR]
  -n <n>, --nfold=<n>             N-fold cross-validation [default: 5]
  --pos-tags=<tags>               Part-of-speech tag prefixes to
                                  include, comma separated J,R,N,V
                                  [default: J,R]
  --top-features=<n>              Do feature selection via TF/IDF information gain.
                                  If zero, include all features
                                  (all included words) [default: 200]
  -f <str>, --feature=<feature>   Feature to predict. rating, rating_class,
                                  rank_class, percentile_rank,
                                  percentile_rank_class. [default: rating_class]
  --rating-category=<category>    Overall, Graphics, Theme, Humor,
                                  Audio, Innovation [default: Overall]
  --entry-type=<regex>            Use comp or jam - not case sensitive
                                  [default: .*]
  --no-performance-metrics        Don't attempt to calculate performance
                                  metrics. Useful when doing blind predictions
                                  on comments without ratings.
  --class-cutoff=<n>              The threshold dividing two classes. Has
                                  different meanings, depending on the
                                  feature being predicted. Defaults to
                                  10 (10th percentile) for percentile_rank and
                                  rank_class (ranked #10 or better),
                                  4.0 for rating_class (scored 4.0 or better).
  --ignore-comment-number         Don't include the number of comments for an
                                  entry as part of the (pre-feature selection)
                                  input vector.
"""
from __future__ import print_function

__version__ = "0.1"

import sys, re, textwrap

from docopt import docopt
from docopt import DocoptExit

# from textblob.taggers import NLTKTagger
from textblob import TextBlob
import pattern
import pattern.vector
from pattern.vector import Document, Model, Classifier, \
    SVM, kfoldcv, count
from pattern.text.en import parsetree
import pattern.metrics

try:
    import json
except ImportError:
    import simplejson as json

options = docopt(__doc__, argv=None, help=True,
                 version=sys.argv[0] + " " + __version__)

# What should we try to predict based on the comments ?
# The "_class" options turn it into binary classification
valid_features = ["rating", "rating_class", "rank_class",
                  "percentile_rank", "percentile_rank_class"]
predict = options["--feature"]
if predict not in valid_features:
    print(__doc__)
    sys.stderr.write("\nInvalid --feature= ... must be one of: " +
                     ', '.join(valid_features) + "\n\n")
    sys.exit()

# Cutoffs for "_class" binary classification
if options["--class-cutoff"] is None:
    # 4 means "Scored 4 or more"
    rating_class_cutoff = 4
    # 10 means "In top 10"
    rank_class_cutoff = 10
    # 10 means "In top 10th percentile"
    percentile_rank_class_cutoff = 10
else:
    rating_class_cutoff = float(options["--class-cutoff"])
    rank_class_cutoff = int(options["--class-cutoff"])
    percentile_rank_class_cutoff = float(options["--class-cutoff"])

# we modify the docopt commandline dict prior to
# outputting the record or options used, so this default
# is properly recorded
if predict == "rating_class":
    options["--class-cutoff"] = rating_class_cutoff
if predict == "rank_class":
    options["--class-cutoff"] = rank_class_cutoff
if predict == "percentile_rank_class":
    options["--class-cutoff"] = percentile_rank_class_cutoff


print(sys.argv[0] + " version " + __version__)
print("Running with options:")
print(options)
print("\n\n----")
print()

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
#rating_category_jam = rating_category+"(Jam)"

#rating_category = "Overall"
#rating_category = "Graphics"

entry_type_regex = re.compile(options["--entry-type"], re.IGNORECASE)

show_performance = not options['--no-performance-metrics']
do_comment_number_hack = not options['--ignore-comment-number']

#nltk_tagger = NLTKTagger()


def discard_words_without_tag_of_interest(text, tag_prefixes=tag_prefixes):
    v = parsetree(text, lemmata=True)[0]
    v = [w.lemma for w in v if w.tag.startswith(tag_prefixes)]
    return v


def discard_words_without_tag_of_interest_textblob(text,
                                                   tag_prefixes=tag_prefixes):
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

# pre-filter to remove entries we don't want, make rating_category keys
# uniform, calculate worst ranking
worst_ranking = 0
filtered_entries = []
for entry in data:
    # skip entries that don't match our specified entry_type
    # (eg, for only Compo or only Jam)
    if entry_type_regex.search(str(entry['entry_type'])) is None:
        continue

    # if we are processing both Compo and Jam entries,
    # we need to account for the two different rating category names
    # (eg "Overall" and "Overall(Jam)" )
    if rating_category in entry['ratings']:
        pass
    elif rating_category+"(Jam)" in entry['ratings']:
        # change any "Overall(Jam)" etc keys as just "Overall"
        entry['ratings'][rating_category] = entry['ratings'].pop(rating_category+"(Jam)")
    elif options["train"]:
        # exclude anything unrated from training, but keep them in predict mode
        continue

    if rating_category in entry['ratings']:
        rank = int(entry['ratings'][rating_category][1])
        worst_ranking = max(rank, worst_ranking)

    filtered_entries.append(entry)

documents = []
for entry in filtered_entries:
    url = entry['url']
    author = entry['author']
    # output vector is the actual rating or class of the entry
    output_vector = None
    if rating_category in entry['ratings']:
        rating = int(round(float(entry['ratings'][rating_category][0])))
        rating_class = (rating >= rating_class_cutoff)  # binary classes

        rank = int(entry['ratings'][rating_category][1])
        rank_class = (
            rank <= rank_class_cutoff)  # top 10 binary classification

        percentile_rank = (float(rank) / float(worst_ranking)) * 100.0
        percentile_rank_class = (
            percentile_rank <= percentile_rank_class_cutoff)

        # a value of one of the above is assigned as the property to predict
        output_vector = vars()[predict]

        """
        # dump csv of author, ranks / ratings and url
        print(
            "{0:s}, {1:d}, {2:s}, {3:d}, "
            "{4:.1f}, {5:s}, {6:s}".format(author,
                                           rating,
                                           repr(rating_class),
                                           rank,
                                           percentile_rank,
                                           repr(percentile_rank_class),
                                           url))
        """

    elif options["train"]:
        # During the judging period entries have no ratings, also
        # those who didn't rate anything (0% Coolness) get no Overall rating.
        # Some entries don't get any ratings (eg, won't run). Some older
        # compos don't have ratings on some entries for inexplicable reasons.
        # We obviously don't attempt to read ratings when there are none.
        sys.stderr.write("Skipping (no ratings field): " + entry['url'] + "\n")
        continue

    all_entry_comment_text_filtered = ""
    entry_comments = []
    for comment in entry['comments']:
        text = comment[3]
        if tag_prefixes:
            text = " ".join(
                discard_words_without_tag_of_interest_textblob(text))
            #text = " ".join(discard_words_without_tag_of_interest(text))

        entry_comments.append(text)

        # document = individual comments
        #vectors.append(Document(text,
        #                        type=output_vector,
        #                        stopwords=True))

    all_entry_comment_text_filtered = " ".join(entry_comments)

    if do_comment_number_hack:
        # this is a HACK, to allow number of comments on the entry to
        # potentially be part of the input vector (if not filtered by
        # feature selection later) we add one instance of this unique word
        # per comment to the document
        all_entry_comment_text_filtered += len(entry_comments) * \
                                           " xxludumscrapecommentcounterxx "

    #print(all_entry_comment_text_filtered)
    # A 'document' is a bag of words from all comments for one game
    # entry (seems to work better grouping all comments), associated with
    # it's rating or classification (eg type=output_vector).
    documents.append(Document(all_entry_comment_text_filtered,
                              name="%s\t%s" % (author, url),
                              type=output_vector,
                              stopwords=True))

vectors = []
if use_feature_selection:
    vectors = Model(documents=documents, weight=pattern.vector.TFIDF)
    vectors = vectors.filter(
        features=vectors.feature_selection(top=select_top_n_features))
    #print(vectors.vectors)
else:
    vectors = documents

if options["train"]:
    if classifier_type == "SVM":
        classifier = SVM(train=vectors,
                         type=svm_type,
                         kernel=svm_kernel)
    else:
        classifier = getattr(pattern.vector, classifier_type)(train=vectors)

    print("Classes: " + repr(classifier.classes))

    #performance = kfoldcv(NB, vectors, folds=n_fold)
    performance = kfoldcv(type(classifier), vectors, folds=n_fold)
    print("Accuracy: %.3f\n" \
          "Precision: %.3f\n" \
          "Recall: %.3f\n" \
          "F1: %.3f\n" \
          "Stddev:%.3f" % performance)
    print()
    print("Confusion matrx:")
    print(classifier.confusion_matrix(vectors).table)

    classifier.save(trained_filename)
elif options["predict"]:
    classifier = Classifier.load(trained_filename)

    print("#Author\tURL\tPrediction\tActual")
    for v in vectors:
        print("%s\t%s\t%s" % (v.name.encode('utf-8'),
                              repr(classifier.classify(v)),
                              repr(v.type)))

    # Remove any individual documents classified as 'None' prior to
    # calculating performance unless the entire set has no classifications,
    # in which case we assume we are doing a blind prediction but won't
    # calculate performance metrics (eg no rating shown on website,
    # so no classification to predict)
    pre_filter_n = len(vectors)
    fvectors = list(filter(lambda x: x.type is not None, vectors))
    post_filter_n = len(fvectors)
    # If every document in the set is labelled as type "None" we are probably
    # working on raw comments without known ratings (eg during judging
    # period), so treat this as a blind prediction and don't do performance
    # metrics
    # Really the user should have added the --no-performance-metrics
    # flag
    if post_filter_n == 0:
        fvectors = vectors
        show_performance = False
    vectors = fvectors

    print("\n----\n")
    if show_performance:
        performance = pattern.metrics.test(classifier.classify, [(d, d.type) for
                                                                 d in vectors])
        if post_filter_n != pre_filter_n:
            print("Discarded %i entries with no ratings field)\n\n"
                  % (pre_filter_n - post_filter_n))

        print("Accuracy: %.3f\n"
              "Precision: %.3f\n"
              "Recall: %.3f\n"
              "F1: %.3f" % performance)
        try:
            print()
            print("Confusion matrx:")
            print(classifier.confusion_matrix(vectors).table)
            print()
        except ValueError:
            pass
        print(textwrap.fill("(Note that performance metrics aren't all that "
                            "meaningful if the model was trained using the "
                            "input data. If the input data wasn't included "
                            "in the training step, it's a good indication "
                            "of how well real-world 'blind' prediction is "
                            "really working)"))
    else:
        print(textwrap.fill("\nNo ratings fields present in input data, so "
                            "no performance metrics can be calculated."))


"""
print("\n\n----")
from example_game_comments import example_game_comments

example_game_comments_filtered = " ".join(discard_words_without_tag_of_interest_textblob(example_game_comments))
print("Example comment words: ")
print(example_game_comments_filtered)
print()
print("Example prediction: " + repr(classifier.classify(Document(example_game_comments_filtered))))
"""