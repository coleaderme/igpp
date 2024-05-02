#!/usr/bin/sh
# copy raw curl command from NETWORKS TAB >> run this script.
echo "$(xsel -o)" | python utils/curly.py
mv utils/secrets_session.py .
