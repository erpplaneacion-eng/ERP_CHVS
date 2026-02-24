import requests
import re

BASE_URL = "http://localhost:8000"
LOGIN_URL = BASE_URL + "/accounts/login/"
NUTRICION_MENUS_URL = BASE_URL + "/nutricion/api/menus/"
NUTRICION_INGREDIENTES_URL = BASE_URL + "/nutricion/api/ingredientes/"

USERNAME = "admin"
PASSWORD = "admin123"
TIMEOUT = 30

def test_get_nutricion_ingredientes_filtered_by_menu_id():
    session = requests.Session()

    # Login step
    resp_get = session.get(LOGIN_URL, timeout=TIMEOUT)
    resp_get.raise_for_status()
    
    csrftoken = session.cookies.get("csrftoken")
    if not csrftoken:
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp_get.text)
        if match:
            csrftoken = match.group(1)
            
    assert csrftoken is not None, "CSRF token not found"
    
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrftoken,
        "next": "/"
    }
    
    session.post(LOGIN_URL, data=login_data, headers={"Referer": LOGIN_URL}, timeout=TIMEOUT)
    assert "sessionid" in session.cookies or len(session.cookies) > 0, "Login failed"

    menus_resp = session.get(NUTRICION_MENUS_URL, timeout=TIMEOUT)
    assert menus_resp.status_code == 200
    menus_json_raw = menus_resp.json()
    
    # Handle DataTables API structure
    if isinstance(menus_json_raw, dict) and "data" in menus_json_raw:
        menus_json = menus_json_raw["data"]
    elif isinstance(menus_json_raw, dict) and "results" in menus_json_raw:
        menus_json = menus_json_raw["results"]
    elif isinstance(menus_json_raw, dict) and "menus" in menus_json_raw:
        menus_json = menus_json_raw["menus"]
    else:
        menus_json = menus_json_raw
        
    assert isinstance(menus_json, list), f"Menus response is not a list: {type(menus_json) if not isinstance(menus_json, dict) else menus_json.keys()}"
    assert len(menus_json) > 0, "Menus list is empty, cannot test ingredientes endpoint without menu_id"

    menu_id = None
    for item in menus_json:
        if isinstance(item, dict):
            if "id_menu" in item:
                menu_id = item["id_menu"]
                break
            elif "id" in item:
                menu_id = item["id"]
                break
            elif "menu_id" in item:
                menu_id = item["menu_id"]
                break
            elif "pk" in item:
                menu_id = item["pk"]
                break
    assert menu_id is not None, "menu_id field not found in menu object"

    # Step 3: Call ingredientes endpoint filtered by menu_id
    params = {"menu_id": menu_id}
    ingredientes_resp = session.get(NUTRICION_INGREDIENTES_URL, params=params, timeout=TIMEOUT)
    ingredientes_resp.raise_for_status()
    ingredientes_json_raw = ingredientes_resp.json()
    
    if isinstance(ingredientes_json_raw, dict) and "data" in ingredientes_json_raw:
        ingredientes_json = ingredientes_json_raw["data"]
    elif isinstance(ingredientes_json_raw, dict) and "results" in ingredientes_json_raw:
        ingredientes_json = ingredientes_json_raw["results"]
    elif isinstance(ingredientes_json_raw, dict) and "ingredientes" in ingredientes_json_raw:
        ingredientes_json = ingredientes_json_raw["ingredientes"]
    else:
        ingredientes_json = ingredientes_json_raw
        
    assert isinstance(ingredientes_json, list), f"Ingredientes response is not a list: {type(ingredientes_json) if not isinstance(ingredientes_json, dict) else ingredientes_json.keys()}"

if __name__ == "__main__":
    test_get_nutricion_ingredientes_filtered_by_menu_id()
