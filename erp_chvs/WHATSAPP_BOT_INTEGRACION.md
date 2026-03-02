# Integración WhatsApp Bot — ERP CHVS

> Documentación técnica del proceso completo de configuración e integración del bot de WhatsApp con el ERP CHVS.
> Creado: 2026-03-01 | Módulo inicial: `calidad` (certificados BPM)

---

## Índice

1. [Arquitectura general](#1-arquitectura-general)
2. [Componentes del sistema](#2-componentes-del-sistema)
3. [Configuración Meta / Facebook](#3-configuración-meta--facebook)
4. [Errores encontrados y soluciones](#4-errores-encontrados-y-soluciones)
5. [Variables de entorno Railway](#5-variables-de-entorno-railway)
6. [Endpoint Django (ERP)](#6-endpoint-django-erp)
7. [Servicio apiw (FastAPI)](#7-servicio-apiw-fastapi)
8. [Lecciones aprendidas](#8-lecciones-aprendidas)
9. [Pasos para agregar un nuevo módulo](#9-pasos-para-agregar-un-nuevo-módulo)

---

## 1. Arquitectura general

```
Usuario WhatsApp
      │  escribe cédula (ej: "1114480905")
      ▼
Meta Cloud API  (número: +57 317 5003012)
      │  webhook POST /webhook
      ▼
[Railway] apiw  (FastAPI — Dalopezos28/apiw)
      │  POST /calidad/api/whatsapp/generar/
      │  Header: X-CALIDAD-API-KEY
      ▼
[Railway] ERP_CHVS  (Django — calidad/views.py)
      │  busca empleado en BD externa (EMPLEADOS_DB_URL)
      │  genera certificado PDF + token firmado HMAC
      ▼
apiw  recibe URL firmada
      │  envía mensaje de texto con link de descarga
      ▼
Usuario WhatsApp  recibe link → descarga PDF
```

---

## 2. Componentes del sistema

| Componente | Plataforma | Repositorio / Ubicación |
|---|---|---|
| `apiw` | Railway — proyecto `developers-facebook` | GitHub: `Dalopezos28/apiw` |
| `ERP_CHVS` | Railway — proyecto `ERP` | GitHub: `Dalopezos28/ERP_CHVS` |
| Número WhatsApp | Meta Business | `+57 317 5003012` (ID: `953575961175366`) |
| WABA | Meta Business | ID: `790999300707445` |
| App Meta | Meta for Developers | `Sistema Notificaciones CHVS` (App ID: `1407600717759524`) |
| System User | Meta Business | `Admin_Bot_CHVS` |

---

## 3. Configuración Meta / Facebook

### 3.1 Verificación del webhook

En **Meta for Developers → App → WhatsApp → Configuration**:

- **Callback URL**: `https://apiw-production.up.railway.app/webhook`
- **Verify Token**: `CHVS_2026` (debe coincidir con `VERIFY_TOKEN` en Railway/apiw)
- **Webhook fields suscritos**: `messages`

El endpoint `GET /webhook` en apiw valida el token y devuelve el challenge:
```python
@app.get("/webhook")
async def validar_webhook(token, challenge):
    if token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
```

### 3.2 WABA — Suscripción de la app (CRÍTICO)

**Este fue el error raíz que impedía recibir mensajes.**

La app debe estar suscrita a la WABA para recibir eventos de webhook. Verificar con:
```bash
curl -X GET \
  "https://graph.facebook.com/v22.0/790999300707445/subscribed_apps" \
  -H "Authorization: Bearer <SYSTEM_USER_TOKEN>"
# Respuesta correcta: {"data":[{"whatsapp_business_api_data":{...}}]}
# Respuesta problema: {"data":[]}  ← sin suscripción = sin webhooks
```

Si `data` está vacío, suscribir con:
```bash
curl -X POST \
  "https://graph.facebook.com/v22.0/790999300707445/subscribed_apps" \
  -H "Authorization: Bearer <SYSTEM_USER_TOKEN>"
# Respuesta esperada: {"success": true}
```

### 3.3 Token del System User (permanente)

Usar siempre un **System User Token** (no token de usuario personal — expira en 24h).

**Dónde generarlo**: `business.facebook.com` → Configuración → Usuarios del sistema → `Admin_Bot_CHVS` → Generar token → seleccionar permisos `whatsapp_business_messaging` y `whatsapp_business_management`.

El token permanente tiene `expires_at: 0`. Guardarlo en Railway como `WHATSAPP_TOKEN` en el servicio `apiw`.

### 3.4 Estado del número de teléfono

El número puede quedar en estado `EXPIRED`. Verificar con:
```bash
curl "https://graph.facebook.com/v22.0/953575961175366" \
  -H "Authorization: Bearer <SYSTEM_USER_TOKEN>"
# Ver campo: "code_verification_status"
```

**Flujo de re-registro si está EXPIRED**:

1. Registrar el número (con PIN de 2FA, usualmente `123456`):
```bash
curl -X POST "https://graph.facebook.com/v22.0/953575961175366/register" \
  -H "Authorization: Bearer <SYSTEM_USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","pin":"123456"}'
```

2. Solicitar código OTP por voz (más confiable que SMS):
```bash
curl -X POST "https://graph.facebook.com/v22.0/953575961175366/request_code" \
  -H "Authorization: Bearer <SYSTEM_USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"code_method":"VOICE","language":"es"}'
```

3. Verificar el código recibido:
```bash
curl -X POST "https://graph.facebook.com/v22.0/953575961175366/verify_code" \
  -H "Authorization: Bearer <SYSTEM_USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"code":"407080"}'
# Respuesta: {"success": true}
```

> **Nota**: `verify_code` tiene rate limit estricto. Si falla, esperar varios minutos antes de reintentar. Solicitar nuevo código con `request_code`.

---

## 4. Errores encontrados y soluciones

### Error 1 — API Key no coincidía

| | Valor |
|---|---|
| `apiw` enviaba | `X-CALIDAD-API-KEY: chvs-calidad-2026-xK9m` |
| ERP tenía | `CALIDAD_WA_API_KEY=chvs-calidad-2026` |

**Solución**: Actualizar `CALIDAD_WA_API_KEY` en Railway/ERP_CHVS con el sufijo correcto.

### Error 2 — Número con estado EXPIRED

Los webhooks de Meta **no se disparan** si el número tiene `code_verification_status: EXPIRED`.

**Síntoma**: Se ven logs en apiw del cron job pero **ningún log de mensajes entrantes**.

**Solución**: Seguir el flujo de re-registro descrito en [sección 3.4](#34-estado-del-número-de-teléfono).

### Error 3 — WABA sin suscripción a la app (error raíz)

Aunque el webhook esté configurado en la consola de Meta, si la app no está suscrita a la WABA, **ningún mensaje llega al webhook**.

**Síntoma**: El webhook de verificación (GET) funciona, pero ningún mensaje real llega.

**Solución**: `POST /{WABA_ID}/subscribed_apps` (ver [sección 3.2](#32-waba--suscripción-de-la-app-crítico)).

### Error 4 — WHATSAPP_TOKEN expirado en Railway

El token de usuario personal (no System User) expira en 24h. Las llamadas a Graph API devuelven error 401.

**Solución**: Generar token permanente de System User (ver [sección 3.3](#33-token-del-system-user-permanente)).

### Error 5 — ERP offline por cron job nocturno

El ERP tiene un cron job en Railway que lo pone en modo offline después de las 9pm Colombia. Los mensajes llegaban a apiw pero el ERP no respondía.

**Solución**: Redeploy manual desde el dashboard de Railway, o ajustar el horario del cron.

---

## 5. Variables de entorno Railway

### Servicio `apiw` (proyecto `developers-facebook`)

| Variable | Valor / Descripción |
|---|---|
| `WHATSAPP_TOKEN` | Token permanente System User `Admin_Bot_CHVS` |
| `PHONE_NUMBER_ID` | `953575961175366` |
| `VERIFY_TOKEN` | `CHVS_2026` |
| `DESTINATARIO` | `573176633526` (o lista separada por comas para el cron) |
| `ERP_URL` | `https://erpchvs-production.up.railway.app` |
| `ERP_API_KEY` | Igual a `CALIDAD_WA_API_KEY` del ERP |
| `GOOGLE_CREDS_JSON` | JSON de Service Account para Google Sheets |

> `DESTINATARIO` **no es una whitelist**. Solo se usa para los reportes programados (cron). Soporta múltiples números separados por coma: `573176633526,573XXXXXXXXX`.

### Servicio `ERP_CHVS` (proyecto `ERP`)

| Variable | Valor / Descripción |
|---|---|
| `CALIDAD_WA_API_KEY` | Clave compartida con `ERP_API_KEY` de apiw |
| `EMPLEADOS_DB_URL` | URL de conexión PostgreSQL a BD externa de empleados |
| `RAILWAY_PUBLIC_DOMAIN` | Auto-detectado por Railway, usado en la URL del certificado |

---

## 6. Endpoint Django (ERP)

**Archivo**: `erp_chvs/calidad/views.py`
**URL**: `POST /calidad/api/whatsapp/generar/`

### Autenticación

Header requerido: `X-CALIDAD-API-KEY: <valor de CALIDAD_WA_API_KEY>`

Comparación segura con `hmac.compare_digest` para evitar timing attacks.

### Flujo interno

```python
@csrf_exempt
def api_whatsapp_generar_certificado(request):
    # 1. Valida API key
    # 2. Parsea JSON → cedula
    # 3. buscar_empleado_por_cedula(cedula) → BD externa PostgreSQL
    # 4. CertificadoCalidad.objects.create(...)
    # 5. _generar_token(cert.pk) → HMAC-SHA256 firmado con SECRET_KEY
    # 6. Construye URL: https://{RAILWAY_PUBLIC_DOMAIN}/calidad/certificados/{pk}/descargar/?token={token}
    # 7. Retorna JSON con numero, nombre, url_certificado
```

### Descarga del certificado (sin sesión)

**URL**: `GET /calidad/certificados/<pk>/descargar/?token=<hmac>`

El token HMAC es válido por 24 horas. Se verifica contra ventanas horarias (actual y anteriores):
```python
def _token_valido(token: str, pk: int) -> bool:
    ventana = int(time.time()) // 3600
    for delta in range(_TOKEN_TTL_HORAS + 1):  # _TOKEN_TTL_HORAS = 24
        msg = f"{pk}:{ventana - delta}".encode()
        esperado = hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()
        if hmac.compare_digest(token, esperado):
            return True
    return False
```

### BD externa de empleados

**Archivo**: `erp_chvs/calidad/services.py`

Consulta tres tablas con `UNION ALL`:
- `tabla_manipuladoras` → tipo `manipuladora`
- `tabla_planta` → tipo `planta`
- `tabla_aprendices` → tipo `aprendiz`

Retorna: `cedula`, `nombre_completo`, `cargo`, `eps`, `programa_empresa`, `tipo_empleado`.

---

## 7. Servicio apiw (FastAPI)

**Repositorio**: `Dalopezos28/apiw`
**Archivo principal**: `main.py`

### Recepción de mensajes (webhook)

```python
@app.post("/webhook")
async def recibir_mensaje(request: Request):
    # Itera entry → changes → messages
    # Para cada mensaje de tipo "text":
    #   Si _es_cedula(texto) → procesar_solicitud_certificado(numero_remitente, cedula)
```

### Validación de cédula

```python
def _es_cedula(texto: str) -> bool:
    """Solo dígitos, entre 6 y 12 caracteres."""
    t = texto.strip()
    return t.isdigit() and 6 <= len(t) <= 12
```

> **Importante**: El usuario debe enviar **únicamente el número** de cédula. Si escribe texto adicional (ej: "mi cédula es 1234567") la validación falla y el mensaje se ignora.

### Sin whitelist de números

El bot responde a **cualquier número** que envíe una cédula válida. No existe filtrado por `from`.

### Cron jobs integrados (reportes de incapacidad)

```python
# 8:00 PM Colombia — reporte diario Google Sheets → WhatsApp
scheduler.add_job(enviar_reporte_whatsapp, 'cron', hour=20, minute=0, timezone='America/Bogota')

# 9:00 AM Colombia — reporte oficial diario
scheduler.add_job(enviar_reporte_whatsapp, 'cron', hour=9, minute=0, timezone='America/Bogota')
```

Los reportes se envían a todos los números listados en `DESTINATARIO` (separados por coma).

---

## 8. Lecciones aprendidas

1. **Suscribir la app a la WABA es obligatorio** y es el paso más fácil de olvidar. Sin esto, cero webhooks llegan aunque todo lo demás esté bien configurado. Siempre verificar `GET /{WABA_ID}/subscribed_apps` primero.

2. **Usar System User Token** desde el inicio. Los tokens de usuario personal expiran en 24h y rompen la integración sin previo aviso.

3. **El estado `EXPIRED` del número bloquea silenciosamente los webhooks**. Si los mensajes no llegan pero el webhook de verificación (GET) funciona, verificar `code_verification_status` del número vía Graph API.

4. **`DESTINATARIO` ≠ whitelist**. Es solo para envíos proactivos/programados. No confundir con control de acceso al bot.

5. **El rate limit de `verify_code` es estricto**. Si se intenta verificar el OTP más de 2–3 veces seguidas, se bloquea temporalmente. Esperar y solicitar nuevo código.

6. **Para OTP preferir VOICE sobre SMS**. Más confiable en Colombia.

7. **El ERP puede estar offline** por cron jobs de ahorro de recursos. Si apiw recibe mensajes pero el ERP no responde, verificar el estado del deploy en Railway.

8. **Probar con `curl` directo al ERP** antes de depurar apiw. Aislar el problema capa por capa:
   - ¿Llega al webhook? → ver logs de apiw
   - ¿Llega al ERP? → `curl -X POST .../calidad/api/whatsapp/generar/`
   - ¿Responde WhatsApp? → ver logs de envío en apiw

---

## 9. Pasos para agregar un nuevo módulo

Para integrar un nuevo módulo del ERP (ej: `logistica`, `nutricion`) con el mismo bot de WhatsApp:

### En el ERP (Django)

1. Crear endpoint en `<modulo>/views.py`:
   - `@csrf_exempt` + validar `X-CALIDAD-API-KEY` con `hmac.compare_digest`
   - Lógica de negocio del módulo
   - Retornar JSON con los datos que enviará el bot

2. Registrar URL en `<modulo>/urls.py`:
   ```python
   path('api/whatsapp/generar/', views.api_whatsapp_<modulo>, name='api_whatsapp_<modulo>'),
   ```

3. Agregar variable de entorno en Railway/ERP si se necesita una API key diferente.

### En apiw (FastAPI)

1. Agregar variable de entorno en Railway/apiw:
   - `ERP_URL_<MODULO>` y `ERP_API_KEY_<MODULO>` (o reutilizar las existentes)

2. En `main.py`, agregar lógica de enrutamiento en el webhook para distinguir qué módulo responde según el contenido del mensaje (ej: palabras clave, prefijos, menú interactivo).

3. Agregar función `procesar_solicitud_<modulo>(numero, dato)` similar a `procesar_solicitud_certificado`.

### Verificación final (checklist)

- [ ] Webhook activo: `GET /{WABA_ID}/subscribed_apps` retorna la app
- [ ] Número activo: `code_verification_status != EXPIRED`
- [ ] `WHATSAPP_TOKEN` es System User Token (permanente)
- [ ] API keys coinciden entre apiw y ERP
- [ ] URL del endpoint es correcta (sin trailing slash issues)
- [ ] ERP desplegado y activo en Railway
- [ ] Prueba directa con `curl` al endpoint ERP antes de probar con WhatsApp

---

*Documentación generada a partir de la sesión de configuración del 2026-03-01.*
