#!/usr/bin/env python

import httpx
import secrets
import sqlite3
import json
import argparse

# textfancy: https://textfancy.com/text-art/
LOGO = """
==============================================
    ▀████▀ ▄▄█▀▀▀█▄█ ▀███▀▀▀██▄▀███▀▀▀██▄ 
      ██ ▄██▀     ▀█   ██   ▀██▄ ██   ▀██▄
      ██ ██▀       ▀   ██   ▄██  ██   ▄██ 
      ██ ██            ███████   ███████  
      ██ ██▄    ▀████  ██        ██       
      ██ ▀██▄     ██   ██        ██       
    ▄████▄ ▀▀███████ ▄████▄    ▄████▄     
==============================================
About: Instagram Profile Picture DL
Github: https://github.com/coleaderme/igpp
Author: coleaderme
License: MIT
"""

# cookies = browser_cookie3.chromium(domain_name="instagram.com")  # cookies from browser!
cookies = secrets.cookies
headers = secrets.headers
data = secrets.data

folder = "downloads_ig"  # default Folder where downloads are saved


def create_db():
    """
    create db if not exist
    """
    try:
        with open("database/igpp.db", "rb") as db:  # noqa
            print("[+] DB exists")
    except:
        print("[+] Creating DB..")
        with sqlite3.connect("database/igpp.db") as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS ig('user' TEXT, 'id' TEXT, 'pic' TEXT, 'hq' TEXT)")
            cur.execute("CREATE UNIQUE INDEX idx_user ON ig(user)")


# comment this after first run.
# create_db()


def is_cached(username: str, conn: sqlite3.Connection) -> tuple or None:
    # trailing comma in sql query is important!
    return conn.cursor().execute("SELECT user FROM ig WHERE user=?;", (username,)).fetchone()


def sql_insert(username: str, user_id: str, url: str, conn: sqlite3.Connection) -> None:
    conn.cursor().execute(
        "INSERT INTO ig(user,id,pic) VALUES(?, ?, ?)",
        (
            username,
            user_id,
            url,
        ),
    )


def sql_update(username: str, url: str, conn: sqlite3.Connection) -> None:
    ''' TODO: how to append to existing data?  '''
    conn.cursor().execute(
        "UPDATE ig SET hq = (?) WHERE user = (?)",
        (
            url,
            username,
        ),
    )


def save(path: str, content: bytes) -> None:
    try:
        with open(path, "wb") as f:
            f.write(content)
    except Exception as save_err:
        print(f"[-] Failed to save to {path}\n", save_err)


def save_csv(data: list[str]) -> None:
    if data:
        print("[+] Saving to CSV..")
        with open("dl.csv", "a") as f:
            for d in data:
                f.write(d + "\n")


def user_info_graphql(user_id: str, username: str, client: httpx.Client) -> str or None:
    """
    return HQ pp url OR False
    this response is just 1.2Kb
    tiny, compared to user_info_api's resp size.
    """
    headers["referer"] = "https://www.instagram.com/" + username
    data = {"variables": '{"id":"xxxxx","render_surface":"PROFILE"}'}
    var_json = json.loads(data["variables"])
    var_json["id"] = user_id
    data["variables"] = json.dumps(var_json)
    # eg, apple looks like: 'variables': '{"id":"5821462185","render_surface":"PROFILE"}',
    try:
        return client.post(url="https://www.instagram.com/api/graphql", headers=headers, data=data).json()["data"]["user"][
            "hd_profile_pic_url_info"
        ]["url"]
    except Exception as graphql_err:
        print(f"[-] user_info_graphql({user_id}, {username}, client)", graphql_err)
        return


def web_profile_info_api(username: str, client: httpx.Client) -> dict or None:
    """get user id from username"""
    print("[+] web_profile_info_api: " + username)
    params = {"username": username}
    r = client.get("https://www.instagram.com/api/v1/users/web_profile_info/", params=params)
    # check if it is an html response, checking first byte of response.
    # left angle bracket '<' is #60 ascii chr.
    if r.content[0] == 60:
        print(f"[-] web_profile_info_api({username}) Not Exist / Logged out ", r.content[:60])
        return
    if r.json().get("data"):
        return r.json()
    print(f"[-] web_profile_info_api({username}) Not Exist / Logged out", r.content[:60])
    return


def user_api(user_id: str, username: str, client: httpx.Client) -> str or None:
    """
    gets bunch of info {dict} about user
    we need HQ url only
    """
    print("[+] user_api: " + username)
    r = client.get(f"https://www.instagram.com/api/v1/users/{user_id}/info/")
    if r.json().get("user"):
        # save(f"{folder}/{username}_ID.json", r.content)
        return r.json()["user"]["hd_profile_pic_url_info"]["url"]
    print(f"[-] user_api({user_id},{username})", r.content[:60])
    return


def query(query: str, client: httpx.Client) -> dict or None:
    # loads values of key 'variables' >> loads json string to dict.
    var_json = json.loads(data["variables"])
    # update value of key 'query'
    var_json["data"]["query"] = query
    # put dict back to json string.
    data["variables"] = json.dumps(var_json)

    r = client.post("https://www.instagram.com/api/graphql", data=data)
    if r.status_code != 200:
        print("[-] Bad request: ", r.content[:60])
        return
    ret = r.json()
    if ret.get("data"):
        return ret["data"]["xdt_api__v1__fbsearch__topsearch_connection"]["users"]
    if ret.get("message"):
        print("[-] " + ret["message"])
        return
    print("[-] error getting response from query:" + query, r.content[:60])
    return


def nodownload(usernames: list, fast: bool = False) -> None:
    print("[+] Getting profile info..")
    with httpx.Client(cookies=cookies, headers=headers, timeout=10) as client, sqlite3.connect("database/igpp.db") as conn:
        for username in usernames:
            if is_cached(username, conn):
                print(f"[/] {username} is cached..skipping")
                continue
            info = web_profile_info_api(username, client)
            if info:
                user_id = info["data"]["user"]["id"]
                print(f"[+] {username}::{user_id}")
                if fast:
                    url = info["data"]["user"]["profile_pic_url_hd"]  # may vary (320px | 150px)
                    sql_insert(username, user_id, url, conn)
                    continue
                # ELSE Get highest quality available.
                # print("[+] Getting HQ..")
                url = user_api(user_id, username, client)
                if url:
                     sql_insert(username, user_id, url, conn)


def download(usernames: list, fast: bool = False) -> None:
    print("[+] Getting profile info..")
    with httpx.Client(cookies=cookies, headers=headers, timeout=10) as client, sqlite3.connect("database/igpp.db") as conn:
        for username in usernames:
            if is_cached(username, conn):
                print(f"{username} is cached..skipping")
                continue
            info = web_profile_info_api(username, client)
            if info:
                user_id = info["data"]["user"]["id"]
                print(f"[+] {username}::{user_id}")
                if fast:
                    url = info["data"]["user"]["profile_pic_url_hd"]  # may vary (320px | 150px)
                    sql_insert(username, user_id, url, conn)
                    save(f"{folder}/{username}_320p.jpg", client.get(url).content)
                    continue
                # ELSE Get highest quality available.
                # print("[+] Getting HQ..")
                url = user_api(user_id, username, client)
                if url:
                    sql_insert(username, user_id, url, conn)
                    save(f"{folder}/{username}.jpg", client.get(url).content)


def search(ig_queries: list[str], count: int, fast: bool = False, no_download: bool = False) -> None:
    usernames = []  # BIG BIG usernames list
    with httpx.Client(cookies=cookies, headers=headers, timeout=10) as client:
        for ig_query in ig_queries:
            print(f"[+] Searching {ig_query}..")
            print("=" * 40)
            users = query(ig_query, client)
            if users:
                if len(users) > count:
                    users = users[:count]
                for u in users:
                    name = u["user"]["username"]
                    # print(name)
                    usernames.append(name)
        # downloads all usernames[..] got from Search()
        if not usernames:
            print(f"[-] failed to get usernames @search({ig_query})")
        if no_download:
            nodownload(usernames, fast)
        else:
            download(usernames, fast)


def main() -> None:
    print(LOGO)
    parser = argparse.ArgumentParser(description="Instagram Profile Picture DL")
    parser.add_argument("-s", "--search", action="store_true", help="Enable search mode")
    parser.add_argument("-c", "--count", type=int, help="show first N search results upto 50 (valid in search mode)")
    parser.add_argument("-f", "--fast", action="store_true", help="Use fast mode, skips extra request")
    parser.add_argument("-n", "--no-download", action="store_true", help="skips photo download")
    parser.add_argument("-i", "--username", nargs="+", help="Input(s) separated by spaces")
    args = parser.parse_args()
    count = args.count
    if count is None:
        count = 5
    if args.search and args.username:
        search(args.username, count, args.fast, args.no_download)
        return
    # direct download
    download(args.username, args.fast)


if __name__ == "__main__":
    main()
