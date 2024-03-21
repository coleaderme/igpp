#!/usr/bin/env python
import httpx
from glob import glob
import json
import asyncio
import browser_cookie3
import secrets
from sys import platform
from subprocess import run
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

cj = browser_cookie3.chromium(domain_name="instagram.com")

FOLDER = "downloads_IG"  # default Folder where downloads are saved
run(["mkdir", FOLDER])


def save(FOLDER: str, name: str, filetype: str, content: bytes):
    try:
        path = FOLDER + "/" + name + "." + filetype
        with open(path, "wb") as f:
            f.write(content)
    except Exception as e:
        print(f"[-] Failed to save to {FOLDER}/{name}\n", e)


async def is_cached_json(username: str) -> bool:
    if platform == "win32":
        cached = glob(f"{FOLDER}\\*.json")
        if f"{FOLDER}\\{username}.json" in cached:
            return True
        return False
    cached = glob(f"{FOLDER}/*.json")
    if f"{FOLDER}/{username}.json" in cached:
        return True
    return False


def not_exist(info: dict) -> bool:
    if info["data"]["user"] is None:
        return True
    return False


## this function gets 2 jsons:
## 1st user.json (gets user id for more info)
## 2nd user_id.json (more info about user)
def download(usernames: str or list, FOLDER=FOLDER, fast=False):
    with httpx.Client(cookies=cj, timeout=10, headers=secrets.headers) as client:
        for username in usernames:
            try:
                if is_cached_json(username):
                    print(f"Skipping Cached: {username:8}")
                    continue  # skip further steps
                # here we'll get user ID from username
                print("[+] Fetching please wait..")
                username_info = client.get(f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}")
                if username_info.text == "":
                    print(f"[-] Empty response, invalid username?: {username_info.content}")
                    continue  # skip further steps
                # caching json response (reduce server calls later) #TODO
                save(
                    FOLDER=FOLDER,
                    name=username,
                    filetype="json",
                    content=username_info.content,
                )
                info = username_info.json()
                if not_exist(info):
                    print(f"[-] User:{username} not exist")
                    continue  # skip further steps
                user_id = info["data"]["user"]["id"]  # user ID
                print(f"[+] User:{username} ID:{user_id}")
                if fast:
                    url = info["data"]["user"]["profile_pic_url_hd"]  # may vary (320px | 150px)
                    save(
                        FOLDER=FOLDER,
                        name=f"{username}_320x",
                        filetype="jpg",
                        content=client.get(url).content,
                    )
                    continue
            except Exception as e:
                print(f"[-] Failed to get user_id from username:{username} ::", e)
                # print(info.content) # for troubleshooting
                continue
            # Get highest quality available (using user ID).
            try:
                user_id_info = client.get(f"https://www.instagram.com/api/v1/users/{user_id}/info/")
                url = user_id_info.json()["user"]["hd_profile_pic_url_info"]["url"]  # HQ pic url
                print(f"[+] HQ: {url}")
                save(
                    FOLDER=FOLDER,
                    name=f"{username}_id",
                    filetype="json",
                    content=user_id_info.content,
                )
                save(
                    FOLDER=FOLDER,
                    name=username,
                    filetype="jpg",
                    content=client.get(url).content,
                )
                print(f"{username}.jpg Downloaded")
            except Exception as e:
                print(f"[-] Failed to get profile info from user_id:{user_id} ::", e)
                print("[-] Inside Exception - HD Profile Pic")
                # print(user_id_info.content) # for troubleshooting
                continue


async def search(ig_queries: list[str], count: int, client):
    data = secrets.data
    variables = json.loads(data["variables"])
    usernames = []  # big list of usernames got from search

    for ig_query in ig_queries:
        print("=" * 46)
        print(f"[+] First [{count}] of {ig_query}")
        print("=" * 46)
        variables["data"]["query"] = ig_query  # updates query name
        data["variables"] = json.dumps(variables)

        try:
            # search query username
            print("[+] Fetching /graphql api..")
            response = await client.post("https://www.instagram.com/api/graphql", data=data)
            users = response.json()["data"]["xdt_api__v1__fbsearch__topsearch_connection"]["users"]
            total_results = len(users)
            print(f"Found {total_results} similar users")
            if count < total_results:
                users = users[:count]  # shorten results list, if less requested.
            # loop over users (got from /graphql api)
            for u in users:
                name = u["user"]["username"]
                print(name)
                usernames.append(name)
        except Exception as e:
            print("[-] Failed to make /graphql request", e)
            print("* Graphql Cookies expired?")
            print("* only --fast mode is avialable.")
            print("> python igpp.py -f -i USER [..]")
            print(response.content)
            return False  # Err exit now.

        print(f"Found {total_results} similar users to:{ig_query}")
    return usernames  # users list[str..]


def main():
    print(LOGO)
    parser = argparse.ArgumentParser(description="Instagram Profile Picture DL")
    parser.add_argument("-s", "--search", action="store_true", help="Enable search mode")
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        help="show first N search results upto 50 (valid in search mode)",
    )
    parser.add_argument("-f", "--fast", action="store_true", help="Use fast mode, skips extra request")
    parser.add_argument("-i", "--username", nargs="+", help="Input(s) separated by spaces")
    args = parser.parse_args()
    if args.search and args.username:
        if args.count is None:
            print("[*] count not specified, will show first 8")
            args.count = 8
        search(ig_queries=args.username, count=args.count, fast=args.fast)
        return True
    if args.username:
        download(usernames=args.username, FOLDER=FOLDER, fast=args.fast)
        return True


async def fetch_data(name, semaphore, client) -> list or bool:
    # if await is_cached_json(name):
    #     print(f'Skipping Cached: {name:8}')
    #     return False
    async with semaphore:
        _info = await client.get(f"https://www.instagram.com/api/v1/users/web_profile_info/?username={name}")

        if _info.text == "" or _info.text.startswith("<"):  # got html, AKA timeout try later.
            print("error making request / soft ban")
            return False
        if _info.status_code == 200:
            await asyncio.sleep(1)  # wait 1 sec per semaphore size
            print("got: " + name)
            return [_info.json(), _info.content, name]  # [dict, bytes, username]
        if _info.status_code == 404:
            print("user not found: " + name)
            return False
        print("some error to get id: " + name)
        print(_info.content)
        return False


async def hq(user_id, name, semaphore, client) -> list or bool:
    async with semaphore:
        _info = await client.get(f"https://www.instagram.com/api/v1/users/{user_id}/info/")

        if _info.text == "":
            print("error making request")
            return False
        if _info.status_code == 200:
            url = _info.json()["user"]["hd_profile_pic_url_info"]["url"]  # HQ url
            print("got hq url: ")
            return [name, url]  # list[str,str]
        print("some to get HQ error: " + user_id)
        print(_info.content)
        return False


async def naim():
    semaphore = asyncio.Semaphore(3)  # Limit to 3 parallel requests
    async with httpx.AsyncClient(cookies=cj, timeout=30, headers=secrets.headers) as client:
        unames = await search(["tinanandi"], 60, client)

        tasks = [fetch_data(uname, semaphore, client) for uname in unames]
        results = await asyncio.gather(*tasks)

        dlls = []  # [[name, url320px, id]..]
        for result in results:
            if result:
                uname = result[2]
                user_id = result[0]["data"]["user"]["id"]  # user ID
                pp = result[0]["data"]["user"]["profile_pic_url_hd"]  # 320px jpg
                print(f"[+] ID:{user_id}::{pp}")
                dlls.append([uname, pp, user_id])  # [[name, url320px, id]..]
        ## for 320px
        # with open(f"{FOLDER}/links.csv",'a') as f:
        #     f.write("name,url\n")
        #     for d in dlls:
        #         f.write(f'{d[0]},{d[1]}\n') # str

        # id is @ 2nd index ; name is @ 0 index
        hqstasks = [hq(i[2], i[0], semaphore, client) for i in dlls]
        completion = await asyncio.gather(*hqstasks)
        ## HQ
        with open(f"{FOLDER}/links.csv", "a") as f:
            f.write("name,url\n")
            for c in completion:
                if c:
                    f.write(f"{c[0]},{c[1]}\n")  # [name, url]

        print("Saved links.csv to " + FOLDER)

def newFunc() -> None:
    with open('asd', 'a') as f:
        



if __name__ == "__main__":
    asyncio.run(naim())
    # main()
