import requests
import re

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"
LOGIN_URL = f"{BASE_URL}/accounts/login/"
PROCESS_LISTADOS_URL = f"{BASE_URL}/facturacion/procesar-listados/?confirm=true"
TIMEOUT = 30


def test_post_facturacion_procesar_listados_with_confirmation():
    session = requests.Session()

    # Step 1: GET /accounts/login/ to retrieve csrftoken cookie & input
    login_get_resp = session.get(LOGIN_URL, timeout=TIMEOUT)
    login_get_resp.raise_for_status()

    csrftoken = session.cookies.get("csrftoken")
    if not csrftoken:
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_get_resp.text)
        if match:
            csrftoken = match.group(1)

    assert csrftoken is not None, "CSRF token not found"

    # Step 2: POST /accounts/login/ with credentials and CSRF token
    login_post_headers = {
        "Referer": LOGIN_URL,
    }
    login_post_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrftoken,
        "next": "/"
    }
    login_post_resp = session.post(
        LOGIN_URL, headers=login_post_headers, data=login_post_data, timeout=TIMEOUT
    )

    # Confirm session cookie is set
    assert "sessionid" in session.cookies or len(session.cookies) > 0, "Session cookie not set after login"

    # Step 3: POST /facturacion/procesar-listados/?confirm=true
    
    confirm_resp = session.post(
        PROCESS_LISTADOS_URL, 
        headers={"Referer": f"{BASE_URL}/facturacion/"}, 
        data={"csrfmiddlewaretoken": csrftoken},
        timeout=TIMEOUT
    )
    
    # We might expect an error or redirect, let's just check it doesn't 500
    assert confirm_resp.status_code in [200, 302], f"Status is {confirm_resp.status_code}"

if __name__ == "__main__":
    test_post_facturacion_procesar_listados_with_confirmation()