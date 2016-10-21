
import requests
from lxml import html
import re

USERNAME = ""
PASSWORD = ""
THREESCALE_ACCOUNT = ""

LOGIN_URL = "https://" + THREESCALE_ACCOUNT + ".3scale.net/p/login"
LOGIN_SESSION_URL = "https://" + THREESCALE_ACCOUNT + ".3scale.net/p/sessions"
URL = "https://" + THREESCALE_ACCOUNT + ".3scale.net/admin/api_docs/services"

def main():
    session_requests = requests.session()

    # Get login csrf token
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
    find_string = "/admin/api_docs/services/"
    start_positions = [match.end() for match in re.finditer(re.escape(find_string), html_string)]

    active_doc_ids = set()
    for position in start_positions:
        matches = re.search('\d+', html_string[position:])
        if matches:
            active_doc_ids.add(matches.group(0))

    for id in active_doc_ids:
        print(session_requests.get("https://" + THREESCALE_ACCOUNT + ".3scale.net/admin/api_docs/services/" + id + ".json").text)


if __name__ == '__main__':
    main()