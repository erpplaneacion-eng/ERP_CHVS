import requests
import re

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"
LOGIN_URL = BASE_URL + "/accounts/login/"
DEPARTAMENTOS_URL = BASE_URL + "/principal/api/departamentos/"
MUNICIPIOS_URL = BASE_URL + "/principal/api/municipios/"
TIMEOUT = 30

def test_get_principal_municipios_filtered_by_departamento_id():
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

    # Step 2: GET departamentos list to pick a valid departamento_id
    dep_resp = session.get(DEPARTAMENTOS_URL, timeout=TIMEOUT)
    dep_resp.raise_for_status()
    departamentos_json = dep_resp.json()
    
    # Handle paginated dict response
    if isinstance(departamentos_json, dict) and "data" in departamentos_json:
        departamentos = departamentos_json["data"]
    elif isinstance(departamentos_json, dict) and "results" in departamentos_json:
        departamentos = departamentos_json["results"]
    elif isinstance(departamentos_json, dict) and "departamentos" in departamentos_json:
        departamentos = departamentos_json["departamentos"]
    else:
        departamentos = departamentos_json
        
    assert isinstance(departamentos, list), f"Departamentos parsed is not a list: {type(departamentos)}. Full: {str(departamentos_json)[:200]}"
    assert len(departamentos) > 0, "No departamentos found to test municipio filter"
    
    valid_departamento_id = None
    for d in departamentos:
        if isinstance(d, dict):
            if "codigo_departamento" in d:
                valid_departamento_id = d["codigo_departamento"]
                break
            elif "id" in d:
                valid_departamento_id = d["id"]
                break
            
    assert valid_departamento_id is not None, "No valid departamento id found"

    # Step 3: GET municipios filtered by departamento_id
    params = {'departamento_id': valid_departamento_id}
    mun_resp = session.get(MUNICIPIOS_URL, params=params, timeout=TIMEOUT)
    mun_resp.raise_for_status()
    municipios_json = mun_resp.json()
    
    if isinstance(municipios_json, dict) and "data" in municipios_json:
        municipios = municipios_json["data"]
    elif isinstance(municipios_json, dict) and "results" in municipios_json:
        municipios = municipios_json["results"]
    elif isinstance(municipios_json, dict) and "municipios" in municipios_json:
        municipios = municipios_json["municipios"]
    else:
        municipios = municipios_json
        
    assert isinstance(municipios, list), f"Municipios parsed is not a list: {type(municipios)}"

if __name__ == "__main__":
    test_get_principal_municipios_filtered_by_departamento_id()
