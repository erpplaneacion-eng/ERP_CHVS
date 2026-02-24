import requests
import re

def test_get_principal_departamentos_with_authorization():
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/accounts/login/"
    departamentos_url = f"{base_url}/principal/api/departamentos/"
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

    # Step 2: GET /principal/api/departamentos/ 
    departamentos_resp = session.get(departamentos_url, timeout=timeout)
    assert departamentos_resp.status_code == 200, f"Failed to get departamentos: status {departamentos_resp.status_code}"

    content_type = departamentos_resp.headers.get("Content-Type", "")
    assert "application/json" in content_type.lower(), f"Response is not JSON, got Content-Type: {content_type}"

    data = departamentos_resp.json()
    assert isinstance(data, (list, dict)), "Response JSON is not a list or dict"

if __name__ == "__main__":
    test_get_principal_departamentos_with_authorization()
