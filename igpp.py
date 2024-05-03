#!/usr/bin/env python

import httpx
import argparse
import secrets_session
import time
import json
# import browser_cookie3

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
cookies = secrets_session.cookies
headers = secrets_session.headers
data = secrets_session.data

folder = "downloads_ig"  # default Folder where downloads are saved


# def valid_instagram_username(username: str) -> bool:
#     pattern = r"^(?!.*\.\.)(?!.*\.$)(?!.*\.\d$)(?!.*\.$)[^\W][\w.]{1,29}$"
#     return bool(re.match(pattern, username))

def holdup(seconds: int=2, hint: str=None)-> None:
    while seconds:
        print(f'Next {hint} in {seconds}s..')
        time.sleep(1)
        seconds -= 1


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


# user_id from username
def web_profile_info_api(username: str, client: httpx.Client) -> dict:
    # print("[+] web_profile_info_api: " + username)
    params = {"username": username}
    r = client.get("https://www.instagram.com/api/v1/users/web_profile_info/", params=params)
    try:
        return r.json()
    except:  # noqa
        print(f"[-] web_profile_info_api({username}) Not Exist / Logged out::", r.content[:60])
        return {}


# method 1 of getting hq pp
def user_api(user_id: str, username: str, client: httpx.Client) -> str:
    """
    gets bunch of info {dict} about user
    we need hq pp url only
    """
    # print("[+] user_api: " + username)
    try:
        return client.get(f"https://www.instagram.com/api/v1/users/{user_id}/info/").json()["user"]["hd_profile_pic_url_info"]["url"]
    except:  # noqa
        print(f"[-] user_api({user_id},{username})")
    return ""


# method 2 of getting hq pp: relies on graphql
def user_info_graphql(user_id: str, username: str, client: httpx.Client) -> str:
    """
    return hq pp url OR None
    this response is just 1.2Kb
    tiny, compared to user_info_api 9Kb.
    """
    headers["referer"] = "https://www.instagram.com/" + username
    data = {"variables": '{"id":"' + user_id + '","render_surface":"PROFILE"}'}
    # eg, apple looks like: 'variables': '{"id":"5821462185","render_surface":"PROFILE"}',
    try:
        return client.post(url="https://www.instagram.com/api/graphql", headers=headers, data=data).json()["data"]["user"]["hd_profile_pic_url_info"]["url"]
    except:  # noqa
        print(f"[-] user_info_graphql({user_id}, {username}, client)")
        return ""


def query(query_term: str, client: httpx.Client) -> dict:
    # 1. access value of key 'variables', loadS json String to dict.
    # 2. update value of key 'query'
    # 3. put dict back to json string.

    var_json = json.loads(data["variables"])
    var_json["data"]["query"] = query_term
    data["variables"] = json.dumps(var_json)

    r = client.post("https://www.instagram.com/api/graphql", data=data)
    try:
        return r.json()["data"]["xdt_api__v1__fbsearch__topsearch_connection"]["users"]
    except:  # noqa
        print(f"[-] query({query}) Logged Out")
        return {}


def download(usernames: list[str], is_fast: bool = False) -> None:
    with httpx.Client(cookies=cookies, headers=headers, timeout=10) as client:
        ig_sso_users = client.post('https://www.instagram.com/api/v1/web/fxcal/ig_sso_users/', cookies=cookies, headers=headers)
        print(f"ig_sso_users:  {ig_sso_users.content}")
        for username in usernames:
            info = web_profile_info_api(username, client)
            if info:
                if info["data"]["user"] is None:
                    print(f"[+] User not exist: {username}")
                    continue  # skip
                user_id = info["data"]["user"]["id"]
                print(f"[+] {username:<20}::{user_id:>12}")
                if is_fast:
                    url = info["data"]["user"]["profile_pic_url_hd"]  # may vary (320px | 150px)
                    save(f"{folder}/{username}_320p.jpg", client.get(url).content)
                    continue
                # ELSE Get highest quality available.
                url = user_api(user_id, username, client)
                if url:
                    save(f"{folder}/{username}.jpg", client.get(url).content)
                holdup(1,'download')


# searching users relies on graphql, means it will break often.
def search(ig_queries: list[str], count: int, is_fast: bool = False) -> None:
    usernames_graphql = []  # BIG BIG usernames list
    with httpx.Client(cookies=cookies, headers=headers, timeout=10) as client:
        for ig_query in ig_queries:
            print(f"[+] Searching for `{ig_query}` please wait..")
            print("===============================================")
            users = query(ig_query, client)
            if users:
                if len(users) > count:
                    users = users[:count]
                for u in users:
                    name = u["user"]["username"]
                    # print(name)
                    usernames_graphql.append(name)
            holdup(5, 'query')
        # downloads all usernames got from Search()
        if not usernames_graphql:
            print(f"[-] failed to get usernames @search({ig_query})")
        else:
            download(usernames_graphql, is_fast)


def main() -> None:
    print(LOGO)
    parser = argparse.ArgumentParser(description="Instagram Profile Picture DL")
    parser.add_argument("-s", "--search", action="store_true", help="Enable search mode")
    parser.add_argument("-c", "--count", type=int, help="show first N search results upto 50 (valid in search mode)")
    parser.add_argument("-f", "--fast", action="store_true", help="Use fast mode, skips extra request")
    parser.add_argument("-i", "--username", nargs="+", help="Input(s) separated by spaces")
    args = parser.parse_args()
    count = args.count
    if count is None:
        count = 5
    if args.search and args.username:
        search(args.username, count, args.fast)
        return
    # direct download
    download(args.username, args.fast)


if __name__ == "__main__":
    main()
