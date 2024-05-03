#!/usr/bin/env python

import httpx
from sys import argv
import secrets_session

INTRO = """
==============================================
About: Instagram Profile Picture DL
Github: https://github.com/coleaderme/igpp
License: MIT
==============================================
"""

cookies = secrets_session.cookies
headers = secrets_session.headers
folder = "pics"  # default: Folder where pictures are saved


def save(path: str, content: bytes) -> None:
    try:
        with open(path, "wb") as f:
            f.write(content)
    except Exception as save_err:
        print(f"[-] Failed to save to {path}\n", save_err)


def web_profile_info_api(username: str, client: httpx.Client) -> dict:
    """user_id from username"""
    print('Getting user id..')
    params = {"username": username}
    r = client.get("https://www.instagram.com/api/v1/users/web_profile_info/", params=params)
    try:
        return r.json()
    except:  # noqa
        print(f"[-] web_profile_info_api({username}) Not Exist / Logged out")
        return {}


def user_api(user_id: str, username: str, client: httpx.Client) -> str:
    """
    Gets bunch of info {dict} about user.
    We need hq pp url only
    """
    print('Getting url..')
    try:
        return client.get(f"https://www.instagram.com/api/v1/users/{user_id}/info/").json()["user"]["hd_profile_pic_url_info"]["url"]
    except:  # noqa
        print(f"[-] user_api({user_id},{username})")
        return ""


def download(usernames: list[str]) -> None:
    with httpx.Client(cookies=cookies, headers=headers, timeout=10) as client:
        for username in usernames:
            print(f'User: {username}')
            info = web_profile_info_api(username, client)
            if not info:
                return  # exit
            if info["data"]["user"] is None:
                print(f"[+] User not exist: {username}")
                continue  # skip
            user_id = info["data"]["user"]["id"]
            # print(f"[+] {username:<20}::{user_id:>12}")
            url = user_api(user_id, username, client)
            if url:  # HQ pic
                save(f"{folder}/{username}.jpg", client.get(url).content)
            else:  # fallback to 320px
                url = info["data"]["user"]["profile_pic_url_hd"]
                save(f"{folder}/{username}.jpg", client.get(url).content)
            print('Done.\n')


def main() -> None:
    if len(argv) < 2:
        print("Usage:\n\tpython igpp.py USERNAME USERNAME2 ...")
        return
    print(INTRO)
    usernames = argv[1:]
    download(usernames)


if __name__ == "__main__":
    main()
