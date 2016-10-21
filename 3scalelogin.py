#!/usr/bin/env python3
import requests
from lxml import html
import re
import configparser
import argparse
import os

config = configparser.ConfigParser()
config.read("config.ini")
USERNAME = config['3scale']['username']
PASSWORD = config['3scale']['password']
THREESCALE_ACCOUNT = config['3scale']['account']
ACTIVEDOCS_PATH = config['3scale']['path']

LOGIN_URL = "https://" + THREESCALE_ACCOUNT + ".3scale.net/p/login"
LOGIN_SESSION_URL = "https://" + THREESCALE_ACCOUNT + ".3scale.net/p/sessions"
URL = "https://" + THREESCALE_ACCOUNT + ".3scale.net/admin/api_docs/services"


def pull():
    session_requests = requests.session()

    # Get login token
    result = session_requests.get(LOGIN_URL)
    tree = html.fromstring(result.text)
    authenticity_token = list(set(tree.xpath("//input[@name='authenticity_token']/@value")))[0]

    # Create payload
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "authenticity_token": authenticity_token,
        "session[remember_me]": "true",
        "commit": "Sign in"
    }

    # Perform login
    session_requests.post(LOGIN_SESSION_URL, data=payload, headers=dict(referer=LOGIN_URL))

    # Scrape url
    result = session_requests.get(URL, headers=dict(referer=URL))
    html_string = result.content.decode('utf-8')
    matches = re.findall('\/admin\/api_docs\/services\/(\d+)\/preview', html_string)

    for id in matches:
        file_content = session_requests.get("https://" + THREESCALE_ACCOUNT + ".3scale.net/admin/api_docs/services/" + id +
                                   ".json").content
        f = open(os.path.expanduser(ACTIVEDOCS_PATH + "/" + id + ".json"), 'wb')
        f.write(file_content)
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process CLI Arguments')
    parser.add_argument('command', choices=['pull', 'push'])
    args = parser.parse_args()

    if args.command == "pull":
        pull()
    elif args.command == "push":
        print("Push time")

