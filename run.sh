#!/bin/sh
EVENT_NUMBER=$1
scrapy crawl ludumdare -o results/results_ld$EVENT_NUMBER.json -t jsonlines -a event_number=$EVENT_NUMBER
