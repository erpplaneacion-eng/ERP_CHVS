import requests
import re

def test_get_facturacion_dashboard_with_valid_session():
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/accounts/login/"
    dashboard_url = f"{base_url}/facturacion/"
    username = "admin"
    password = "admin123"
    timeout = 30

    session = requests.Session()
    
    # Login step
    resp_get = session.get(login_url, timeout=timeout)
    resp_get.raise_for_status()
    
    csrftoken = session.cookies.get("csrftoken")
    if not csrftoken:
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp_get.text)
        if match:
            csrftoken = match.group(1)
            
    assert csrftoken is not None, "CSRF token not found"
    
    login_data = {
        "username": username,
        "password": password,
        "csrfmiddlewaretoken": csrftoken,
        "next": "/"
    }
    
    session.post(login_url, data=login_data, headers={"Referer": login_url}, timeout=timeout)
    
    assert "sessionid" in session.cookies or len(session.cookies) > 0, "Login failed"

    # Step 2: GET the facturacion dashboard with session cookie
    dashboard_resp = session.get(dashboard_url, timeout=timeout)
    dashboard_resp.raise_for_status()

    # Validate response is HTML
    content_type = dashboard_resp.headers.get("Content-Type", "")
    assert "text/html" in content_type.lower(), f"Expected HTML content but got Content-Type: {content_type}"
    assert dashboard_resp.text.strip(), "Empty response body received from dashboard endpoint"

if __name__ == "__main__":
    test_get_facturacion_dashboard_with_valid_session()
