import requests
import re

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"
TIMEOUT = 30

def test_get_nutricion_menus_with_authorization():
    session = requests.Session()
    try:
        # Step 1: GET login page to get csrftoken
        login_url = f"{BASE_URL}/accounts/login/"
        login_get_resp = session.get(login_url, timeout=TIMEOUT)
        assert login_get_resp.status_code == 200, "Failed to load login page"

        csrftoken = session.cookies.get("csrftoken")
        if not csrftoken:
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_get_resp.text)
            if match:
                csrftoken = match.group(1)

        assert csrftoken is not None, "CSRF token not found"

        # Step 2: POST login credentials with CSRF token
        login_headers = {
            "Referer": login_url,
        }
        login_data = {
            "username": USERNAME,
            "password": PASSWORD,
            "csrfmiddlewaretoken": csrftoken,
            "next": "/"
        }
        login_post_resp = session.post(login_url, data=login_data, headers=login_headers, timeout=TIMEOUT)

        # Confirm session cookie is set
        sessionid = session.cookies.get("sessionid", None)
        assert sessionid, "No sessionid cookie set after login"

        # Step 3: GET nutricion menus with authenticated session
        menus_resp = session.get(f"{BASE_URL}/nutricion/api/menus/", timeout=TIMEOUT)
        assert menus_resp.status_code == 200, f"Failed to get nutricion menus, status code {menus_resp.status_code}"

        menus_json_raw = menus_resp.json()
        
        if isinstance(menus_json_raw, dict) and "data" in menus_json_raw:
            menus_json = menus_json_raw["data"]
        elif isinstance(menus_json_raw, dict) and "results" in menus_json_raw:
            menus_json = menus_json_raw["results"]
        elif isinstance(menus_json_raw, dict) and "menus" in menus_json_raw:
            menus_json = menus_json_raw["menus"]
        else:
            menus_json = menus_json_raw

        assert isinstance(menus_json, list), f"Response is not a JSON list: {type(menus_json)}"
        
    finally:
        session.close()

if __name__ == "__main__":
    test_get_nutricion_menus_with_authorization()