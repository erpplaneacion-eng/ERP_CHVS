# Load Testing ERP_CHVS (Locust)

Este paquete ejecuta pruebas de carga del ERP con:

- Login real Django (`/accounts/login/`) con sesión + CSRF.
- Escenarios por rol: facturación, contabilidad, agente.
- Suites por etiqueta: `core`, `heavy`, `ia`.

## 1. Instalación

Desde `erp_chvs/`:

```bash
pip install -r loadtest/requirements-loadtest.txt
```

## 2. Variables de entorno mínimas

Requeridas (fallback común):

- `LT_USER`
- `LT_PASSWORD`

Opcional por rol:

- `LT_FACT_USER`, `LT_FACT_PASSWORD`
- `LT_CONT_USER`, `LT_CONT_PASSWORD`
- `LT_AGENTE_USER`, `LT_AGENTE_PASSWORD`

Opcionales de contexto:

- `LT_PROGRAMA_ID`
- `LT_FOCALIZACION`
- `LT_MES` (ejemplo: `ABRIL`)
- `LT_MODALIDAD_ID` (si quieres forzar modalidad de agente)
- `LT_COMPLEMENTO` (default: `CAP AM`)
- `LT_ENABLE_AGENTE_GENERAR` (`true|false`, default `false`)

## 3. Ejecución rápida

### PowerShell (Windows)

Desde `erp_chvs/`:

```powershell
$env:LT_USER="usuario_pruebas"
$env:LT_PASSWORD="password_pruebas"
python -m locust -f loadtest/locustfile.py --headless --host https://tu-app.up.railway.app -u 30 -r 5 --run-time 5m --tags core --html loadtest/reports/core.html --csv loadtest/reports/core
```

### Bash (Linux/macOS)

```bash
export LT_USER="usuario_pruebas"
export LT_PASSWORD="password_pruebas"
python -m locust -f loadtest/locustfile.py --headless --host https://tu-app.up.railway.app -u 30 -r 5 --run-time 5m --tags core --html loadtest/reports/core.html --csv loadtest/reports/core
```

## 4. Plan completo automatizado

### Windows

```powershell
.\loadtest\run_load_tests.ps1 -HostUrl "https://tu-app.up.railway.app"
```

### Linux/macOS

```bash
chmod +x loadtest/run_load_tests.sh
./loadtest/run_load_tests.sh "https://tu-app.up.railway.app"
```

El plan corre:

1. Baseline `core` (5, 10, 20, 30 usuarios)
2. Stress `core` (40, 50)
3. `heavy` (PDF/ZIP)
4. `ia` (NIA/Gemini)
5. Soak `core` (30 usuarios, 20 minutos)

## 5. Qué valida cada suite

- `core`: navegación y APIs frecuentes de módulos principales.
- `heavy`: generación de PDF y ZIP masivo de facturación.
- `ia`: `/dashboard/api/nia/chat/` y reset de sesión NIA.

`ia` opcionalmente puede disparar `/agente/api/generar/` si defines:

```bash
LT_ENABLE_AGENTE_GENERAR=true
```

## 6. Criterios sugeridos de aceptación

- Error rate `< 1%` en `core`.
- `p95` en `core` `< 800ms` (o umbral acordado por negocio).
- `heavy` sin 5xx sostenidos ni timeouts en ráfagas cortas.
- `ia` con latencia estable y sin aumento abrupto de errores.

## 7. Notas operativas

- Ejecuta idealmente en ventana controlada (staging o baja actividad).
- Usa usuarios con grupos correctos para evitar 403 por RBAC.
- Si no hay datos de programa/focalización/sede en BD, la suite `heavy` no tendrá cobertura útil.
