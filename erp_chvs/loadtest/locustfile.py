import os
import re
import time
from datetime import datetime
from typing import Dict, Optional

from locust import HttpUser, between, task, tag, events


DEFAULT_WAIT_MIN = float(os.getenv("LT_WAIT_MIN_SECONDS", "0.8"))
DEFAULT_WAIT_MAX = float(os.getenv("LT_WAIT_MAX_SECONDS", "2.5"))

# Credenciales base (fallback)
LT_USER = os.getenv("LT_USER", "")
LT_PASSWORD = os.getenv("LT_PASSWORD", "")

# Credenciales por rol (si no se definen, usa fallback base)
LT_FACT_USER = os.getenv("LT_FACT_USER", LT_USER)
LT_FACT_PASSWORD = os.getenv("LT_FACT_PASSWORD", LT_PASSWORD)
LT_CONT_USER = os.getenv("LT_CONT_USER", LT_USER)
LT_CONT_PASSWORD = os.getenv("LT_CONT_PASSWORD", LT_PASSWORD)
LT_AGENTE_USER = os.getenv("LT_AGENTE_USER", LT_USER)
LT_AGENTE_PASSWORD = os.getenv("LT_AGENTE_PASSWORD", LT_PASSWORD)

LT_TIMEOUT_SECONDS = float(os.getenv("LT_TIMEOUT_SECONDS", "60"))
LT_VERIFY_SSL = os.getenv("LT_VERIFY_SSL", "true").lower() == "true"
LT_ENABLE_AGENTE_GENERAR = os.getenv("LT_ENABLE_AGENTE_GENERAR", "false").lower() == "true"
LT_SUITE = os.getenv("LT_SUITE", "core").strip().lower()

LT_MODALIDAD_ID = os.getenv("LT_MODALIDAD_ID", "")
LT_FOCALIZACION = os.getenv("LT_FOCALIZACION", "")
LT_PROGRAMA_ID = os.getenv("LT_PROGRAMA_ID", "")
LT_MES = os.getenv("LT_MES", "")
LT_COMPLEMENTO = os.getenv("LT_COMPLEMENTO", "CAP AM")
LT_NIA_PROMPT = os.getenv(
    "LT_NIA_PROMPT",
    "Resume en una frase el estado del modulo de facturacion para pruebas de carga.",
)

# IDs de modalidad conocidos por el proyecto (fallback si no se especifica LT_MODALIDAD_ID).
MODALIDAD_CANDIDATAS = ["020511", "020701", "20501", "20502", "20503", "20507", "20510"]

MESES_ES = [
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
]

_warned_missing_credentials = False


def _current_month_es() -> str:
    return MESES_ES[datetime.now().month - 1]


def _extract_csrf_token_from_html(html: str) -> Optional[str]:
    match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html)
    return match.group(1) if match else None


def _safe_json(resp) -> Dict:
    try:
        return resp.json()
    except Exception:
        return {}


@events.test_start.add_listener
def _validate_credentials(environment, **kwargs):
    global _warned_missing_credentials
    if _warned_missing_credentials:
        return
    if not LT_USER and not LT_FACT_USER and not LT_CONT_USER and not LT_AGENTE_USER:
        _warned_missing_credentials = True
        environment.runner.quit()
        raise RuntimeError(
            "Faltan credenciales. Define LT_USER/LT_PASSWORD o credenciales por rol (LT_FACT_*, LT_CONT_*, LT_AGENTE_*)."
        )


class BaseERPUser(HttpUser):
    abstract = True
    wait_time = between(DEFAULT_WAIT_MIN, DEFAULT_WAIT_MAX)

    username = LT_USER
    password = LT_PASSWORD

    programa_id: Optional[str] = None
    focalizacion: Optional[str] = None
    sede_nombre: Optional[str] = None
    sede_cod: Optional[str] = None
    mes: Optional[str] = None
    modalidad_id: Optional[str] = None

    def on_start(self):
        self.client.verify = LT_VERIFY_SSL
        self.client.timeout = LT_TIMEOUT_SECONDS
        self._login()
        self._discover_context()

    def on_stop(self):
        self.client.get("/accounts/logout/", name="auth:logout")

    def _login(self):
        if not self.username or not self.password:
            raise RuntimeError(
                f"Credenciales vacias para {self.__class__.__name__}. "
                "Define variables LT_USER/LT_PASSWORD o credenciales por rol."
            )

        login_get = self.client.get("/accounts/login/", name="auth:login_page")
        if login_get.status_code != 200:
            raise RuntimeError(f"No se pudo abrir login. HTTP {login_get.status_code}")

        csrf_token = self.client.cookies.get("csrftoken") or _extract_csrf_token_from_html(login_get.text)
        if not csrf_token:
            raise RuntimeError("No se encontro CSRF token en la pagina de login.")

        data = {
            "username": self.username,
            "password": self.password,
            "csrfmiddlewaretoken": csrf_token,
            "next": "/dashboard/",
        }
        headers = {
            "Referer": f"{self.host}/accounts/login/",
        }

        login_post = self.client.post(
            "/accounts/login/",
            data=data,
            headers=headers,
            allow_redirects=False,
            name="auth:login_submit",
        )

        if login_post.status_code not in (302, 303):
            raise RuntimeError(f"Login fallido. HTTP {login_post.status_code}")

        location = login_post.headers.get("Location", "")
        if "login" in location.lower():
            raise RuntimeError("Login rechazado: redirigido nuevamente al formulario.")

    def _discover_context(self):
        self.mes = (LT_MES or _current_month_es()).upper()
        self.modalidad_id = LT_MODALIDAD_ID or None

        candidate_program_ids = []
        if LT_PROGRAMA_ID:
            candidate_program_ids.append(str(LT_PROGRAMA_ID))

        # Usa API de agente para obtener programas activos.
        r_prog = self.client.get("/agente/api/programas/", name="ctx:agente_programas")
        if r_prog.status_code == 200:
            payload = _safe_json(r_prog)
            for item in payload.get("programas", []):
                pid = str(item.get("id", "")).strip()
                if pid and pid not in candidate_program_ids:
                    candidate_program_ids.append(pid)

        for pid in candidate_program_ids:
            focal = LT_FOCALIZACION
            if not focal:
                r_f = self.client.get(
                    f"/facturacion/api/get-focalizaciones-for-programa/?programa_id={pid}",
                    name="ctx:focalizaciones",
                )
                if r_f.status_code == 200:
                    payload = _safe_json(r_f)
                    focals = payload.get("focalizaciones", [])
                    if focals:
                        focal = str(focals[0])

            r_s = self.client.get(
                f"/facturacion/api/get-sedes-completas/?programa_id={pid}",
                name="ctx:sedes_completas",
            )
            if r_s.status_code != 200:
                continue

            sedes_payload = _safe_json(r_s)
            sedes = sedes_payload.get("sedes", [])
            if not sedes:
                continue

            self.programa_id = pid
            self.focalizacion = focal or LT_FOCALIZACION or "F1"
            self.sede_nombre = sedes[0].get("nombre")
            self.sede_cod = sedes[0].get("cod_interprise")
            break

        # Si no pudo descubrir programa/sede, deja valores para que los endpoints se salten.
        if not self.programa_id and LT_PROGRAMA_ID:
            self.programa_id = str(LT_PROGRAMA_ID)
            self.focalizacion = LT_FOCALIZACION or "F1"

        if not self.modalidad_id:
            for mid in MODALIDAD_CANDIDATAS:
                r_pool = self.client.get(
                    f"/agente/api/lote/pool-disponible/?modalidad_id={mid}",
                    name="ctx:modalidad_pool_probe",
                )
                if r_pool.status_code == 200:
                    self.modalidad_id = mid
                    break

    def _json_post(self, path: str, payload: Dict, name: str):
        headers = {"Content-Type": "application/json"}
        return self.client.post(path, json=payload, headers=headers, name=name)


class FacturacionCoreUser(BaseERPUser):
    username = LT_FACT_USER
    password = LT_FACT_PASSWORD
    weight = int(os.getenv("LT_WEIGHT_FACT", "5")) if LT_SUITE == "core" else 0

    @tag("core")
    @task(5)
    def dashboard(self):
        self.client.get("/dashboard/", name="core:dashboard")

    @tag("core")
    @task(4)
    def facturacion_pages(self):
        self.client.get("/facturacion/", name="core:facturacion_home")
        self.client.get("/facturacion/reportes-asistencia/", name="core:facturacion_reportes")

    @tag("core")
    @task(4)
    def facturacion_api_light(self):
        if not self.programa_id:
            return
        self.client.get(
            f"/facturacion/api/focalizaciones-existentes/?programa_id={self.programa_id}",
            name="core:api_focalizaciones_existentes",
        )
        self.client.get(
            f"/facturacion/api/get-focalizaciones-for-programa/?programa_id={self.programa_id}",
            name="core:api_focalizaciones_programa",
        )
        self.client.get(
            f"/facturacion/api/get-sedes-completas/?programa_id={self.programa_id}",
            name="core:api_sedes_completas",
        )

    @tag("core")
    @task(2)
    def conteo_estudiantes(self):
        if not all([self.programa_id, self.sede_nombre, self.focalizacion]):
            return
        self.client.get(
            "/facturacion/api/conteo-estudiantes-por-nivel/"
            f"?programa_id={self.programa_id}"
            f"&sede_nombre={self.sede_nombre}"
            f"&focalizacion={self.focalizacion}"
            f"&complemento={LT_COMPLEMENTO}",
            name="core:api_conteo_estudiantes",
        )


class ContabilidadCoreUser(BaseERPUser):
    username = LT_CONT_USER
    password = LT_CONT_PASSWORD
    weight = int(os.getenv("LT_WEIGHT_CONT", "3")) if LT_SUITE == "core" else 0

    @tag("core")
    @task(4)
    def contabilidad_pages(self):
        self.client.get("/contabilidad/", name="core:contabilidad_home")
        self.client.get("/contabilidad/mis-registros/", name="core:contabilidad_mis_registros")

    @tag("core")
    @task(4)
    def contabilidad_api(self):
        self.client.get("/contabilidad/api/registros/", name="core:contabilidad_api_registros")
        self.client.get("/contabilidad/api/dashboard-unificado/", name="core:contabilidad_api_dashboard_unificado")


class AgenteCoreUser(BaseERPUser):
    username = LT_AGENTE_USER
    password = LT_AGENTE_PASSWORD
    weight = int(os.getenv("LT_WEIGHT_AGENTE", "2")) if LT_SUITE == "core" else 0

    @tag("core")
    @task(4)
    def agente_pages_and_reads(self):
        self.client.get("/agente/", name="core:agente_home")
        self.client.get("/agente/generar-lote/", name="core:agente_generar_lote")
        self.client.get("/agente/api/programas/", name="core:agente_api_programas")

    @tag("core")
    @task(3)
    def agente_pool_read(self):
        if not self.modalidad_id:
            return
        self.client.get(
            f"/agente/api/lote/pool-disponible/?modalidad_id={self.modalidad_id}",
            name="core:agente_api_pool_disponible",
        )


class HeavyFacturacionUser(BaseERPUser):
    username = LT_FACT_USER
    password = LT_FACT_PASSWORD
    weight = int(os.getenv("LT_WEIGHT_HEAVY", "1")) if LT_SUITE == "heavy" else 0

    @tag("heavy")
    @task(2)
    def generar_pdf_asistencia(self):
        if not all([self.programa_id, self.sede_cod, self.focalizacion, self.mes]):
            return
        self.client.get(
            f"/facturacion/generar-asistencia/{self.programa_id}/{self.sede_cod}/{self.mes}/{self.focalizacion}/",
            name="heavy:facturacion_pdf_asistencia",
        )

    @tag("heavy")
    @task(1)
    def generar_zip_masivo(self):
        if not all([self.programa_id, self.focalizacion, self.mes]):
            return
        self.client.get(
            f"/facturacion/generar-zip-masivo/{self.programa_id}/{self.mes}/{self.focalizacion}/",
            name="heavy:facturacion_zip_masivo",
        )


class IAUser(BaseERPUser):
    username = LT_AGENTE_USER
    password = LT_AGENTE_PASSWORD
    weight = int(os.getenv("LT_WEIGHT_IA", "1")) if LT_SUITE == "ia" else 0

    @tag("ia")
    @task(4)
    def nia_chat(self):
        payload = {"mensaje": LT_NIA_PROMPT}
        self._json_post("/dashboard/api/nia/chat/", payload, name="ia:dashboard_nia_chat")

    @tag("ia")
    @task(2)
    def nia_reset(self):
        self._json_post("/dashboard/api/nia/reset/", {}, name="ia:dashboard_nia_reset")

    @tag("ia")
    @task(1)
    def agente_generar_optional(self):
        if not LT_ENABLE_AGENTE_GENERAR:
            return
        if not self.modalidad_id:
            return

        with self.client.post(
            "/agente/api/generar/",
            json={"modalidad_id": self.modalidad_id},
            headers={"Content-Type": "application/json"},
            name="ia:agente_generar",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
                return
            body = _safe_json(resp)
            if not body.get("ok"):
                resp.failure(f"agente/api/generar response not ok: {body}")
                return
            generacion_id = body.get("generacion_id")
            if not generacion_id:
                resp.failure("agente/api/generar sin generacion_id")
                return
            resp.success()

        # Poll rapido para observar estado sin mantener la transaccion abierta.
        for _ in range(2):
            self.client.get(
                f"/agente/api/generar/{generacion_id}/estado/",
                name="ia:agente_estado_generacion",
            )
            time.sleep(0.3)
