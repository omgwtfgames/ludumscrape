#!/bin/sh
EVENT_NUMBER=$1
if [ ! -z "$SCRAPY_BIN" ]; then
  SCRAPY_BIN="scrapy"
fi
mkdir -p .job
JOBDIR=.job/$1
mkdir -p $JOBDIR
$SCRAPY_BIN crawl ludumdare -o results/results_ld$EVENT_NUMBER.json -t jsonlines \
                            -a event_number=$EVENT_NUMBER -s JOBDIR=$JOBDIR
