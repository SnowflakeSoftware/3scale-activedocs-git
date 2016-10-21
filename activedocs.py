#!/usr/bin/env python3
import requests
from lxml import html
import re
import configparser
import argparse
import os

config_directory = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(config_directory + "/config.ini")
USERNAME = config['3scale']['username']
PASSWORD = config['3scale']['password']
THREESCALE_ACCOUNT = config['3scale']['account']
THREESCALE_ACCESS_TOKEN = config['3scale']['access_token']
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
    regex = re.compile('/api_docs/services/(\d+)/preview" title="Preview service spec">([^<]+)</a></td><td>([^<]+)')
    matches = regex.finditer(html_string)

    map_file = open(os.path.expanduser(ACTIVEDOCS_PATH + "/map_file"), 'w+')
    for match in matches:
        match_url = "https://" + THREESCALE_ACCOUNT + ".3scale.net/admin/api_docs/services/" + match.group(1) + ".json"
        print("Downloading " + match.group(3) + ".json")
        file_content = session_requests.get(match_url).content
        json_file = open(os.path.expanduser(ACTIVEDOCS_PATH + "/" + match.group(3) + ".json"), 'wb')
        json_file.write(file_content)
        json_file.close()

        map_file.write(match.group(3) + ".json" + "," + match.group(1) + "\n")

    map_file.close()


def push(filename):
    if not filename or ".json" not in filename:
        print("Please enter a filename ending in '.json' to push.")
    map_file = open(os.path.expanduser(ACTIVEDOCS_PATH + "/map_file"), 'r')
    for map_file_line in map_file:
        map_list = map_file_line.split(',')
        if map_list[0] == filename:
            json_file = open(os.path.expanduser(ACTIVEDOCS_PATH + "/" + map_list[0]), 'r')
            json_contents = {"body": json_file.read()}
            api_url = 'https://' + THREESCALE_ACCOUNT + '.3scale.net/admin/api/active_docs/' + map_list[1].rstrip() + \
                      '.xml?access_token=' + THREESCALE_ACCESS_TOKEN
            print("Pushing " + map_list[0] + " to " + api_url)
            put_request = requests.put(api_url, json_contents)
            print(put_request.status_code)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process CLI Arguments')
    parser.add_argument('command', choices=['pull', 'push'])
    parser.add_argument('--filename', required=False)
    args = parser.parse_args()

    if args.command == "pull":
        pull()
    elif args.command == "push":
        push(args.filename)
