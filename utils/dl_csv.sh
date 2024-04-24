#!/usr/bin/env bash

# Check if links.csv file exists
if [ ! -f "links.csv" ]; then
    echo "Error: links.csv file not found."
    exit 1
fi

# Read each line from links.csv
while IFS=, read -r name url; do
    # Skip empty lines or lines starting with a comment symbol #
    if [[ -z "$name" || -z "$url" || "$name" == \#* ]]; then
        continue
    fi

    # Download the URL using aria2c with proper naming
    aria2c -o "$name" "$url"
done < "links.csv"
