#!/usr/bin/env python
# USAGE: echo $(xsel -o) | ./curly.py
# USAGE: echo $(xsel -o) | python curly.py
#
# Reads raw curl commands from `raw.txt`
# process..
# Saves to `secrets.py`
# (in your script)
# import secrets
# cookies = secrets.cookies
# headers = secrets.headers
# data = secrets.data
#
from urllib.parse import unquote
from sys import stdin

print("USAGE: echo $(xsel -o) | ./curly.py\nEXIT now Ctrl+C\nelse will stay hung on this stage.\n")

curl = stdin.read()
curl = unquote(curl)  # parse encoded urls


def getHeaders_stdin(curl: str) -> dict:
    headers = {}
    # for v in line.split('   '):
    for v in curl.split(" \\"):
        v = v.strip()
        if v.startswith("-H"):
            if "cookie:" in v:
                continue  # skip then
            v = v[4:-1]
            # print("[1]"+v)
            key, value = v.split(":", 1)
            headers[key.strip()] = value.strip()
    return headers


def getCookies_stdin(curl: str) -> dict:
    cookies = {}
    for v in curl.split(" \\"):
        v = v.strip()
        if v.startswith("-H") and "cookie" in v:
            v = v[12:-1]
            for e in v.split(";"):
                key, value = e.split("=", 1)
                cookies[key.strip()] = value.strip()
    return cookies


def getData_stdin(curl: str) -> dict:
    data = {}
    for v in curl.split(" \\"):
        v = v.strip()
        if v.startswith("--data-raw"):
            v = v[12:-1]
            for e in v.split("&"):
                key, value = e.split("=", 1)
                data[key.strip()] = value.strip()
    return data


def getHeaders(curl: str) -> dict:
    headers = {}
    for line in curl.split("\n")[1:-1]:
        line = line.strip()
        for v in line.split("   "):
            v = v.strip()
            if v.startswith("-H"):
                if "cookie:" in v:
                    continue  # skip then
                v = v[4:-3]
                key, value = v.split(":", 1)
                headers[key.strip()] = value.strip()
    return headers


def getCookies(curl: str) -> dict:
    cookies = {}
    for line in curl.split("\n")[1:-1]:
        line = line.strip()
        for v in line.split("   "):
            v = v.strip()
            if v.startswith("-H") and "cookie" in v:
                v = v[12:-3]
                for e in v.split(";"):
                    key, value = e.split("=", 1)
                    cookies[key.strip()] = value.strip()
    return cookies


def getData(curl: str) -> dict:
    data = {}
    for line in curl.split("\n"):
        line = line.strip()
        for v in line.split("   "):
            v = v.strip()
            if v.startswith("--data-raw"):
                v = v[12:-3]
                for e in v.split("&"):
                    key, value = e.split("=", 1)
                    data[key.strip()] = value.strip()
    return data


h = getHeaders_stdin(curl)
c = getCookies_stdin(curl)
d = getData_stdin(curl)


def read_from_file():
    with open("raw.txt", "r") as f:
        curl = f.read()
    curl = unquote(curl)  # parse encoded urls
    h = getHeaders_stdin(curl)
    c = getCookies_stdin(curl)
    d = getData_stdin(curl)
    with open("secrets.py", "w") as f:
        f.write(f"cookies={c}\nheaders={h}\ndata={d}")
    print("[+] Saved cookies to file")

## prints all
print(h)
print(c)
print(d)

## saves to file
with open("secrets_session.py", "w") as f:
    f.write(f"cookies={c}\nheaders={h}\ndata={d}")
print("\n[+] Saved cookies to file")
