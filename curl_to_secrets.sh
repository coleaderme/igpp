#!/usr/bin/sh
# copy raw curl command from NETWORKS TAB >> run this script.
printf "$(xsel -o)" | python utils/curly.py
