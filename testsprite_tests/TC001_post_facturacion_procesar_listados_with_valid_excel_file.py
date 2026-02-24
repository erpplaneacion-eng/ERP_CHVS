import requests
import re

def test_post_facturacion_procesar_listados_with_valid_excel_file():
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/accounts/login/"
    facturacion_url = f"{base_url}/facturacion/"
    procesar_listados_url = f"{base_url}/facturacion/procesar-listados/"
    username = "admin"
    password = "admin123"
    timeout = 30
    session = requests.Session()

    try:
        # Step 1: Login
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

        # Step 2: GET /facturacion/ to get CSRF token cookie (optional but good idea)
        dashboard_resp = session.get(facturacion_url, timeout=timeout)
        assert dashboard_resp.status_code == 200, f"Failed to get dashboard, status {dashboard_resp.status_code}"
        
        csrftoken = session.cookies.get("csrftoken") or csrftoken

        # Step 3: POST to /facturacion/procesar-listados/ with file and CSRF token header
        files = {
            "archivo": ("SIMAT_Lote3.xlsx", b"PK\x03\x04\x14\x00\x06\x00", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        procesar_headers = {
            "Referer": facturacion_url
        }
        procesar_data = {
            "csrfmiddlewaretoken": csrftoken
        }

        procesar_resp = session.post(procesar_listados_url, files=files, data=procesar_data, headers=procesar_headers, timeout=timeout)
        assert procesar_resp.status_code == 200, f"POST procesar-listados failed with status {procesar_resp.status_code}"
        
        print("TC001 passed successfully")

    finally:
        session.close()

if __name__ == "__main__":
    test_post_facturacion_procesar_listados_with_valid_excel_file()
