# CLAUDE.md — Maestro

ERP Django 5.2.5 para el **Programa de Alimentación Escolar (PAE)** de Colombia. Maneja listas de focalización, planificación nutricional, gestión institucional y generación de menús con IA.

**Requisitos**: Python 3.13+, PostgreSQL

---

## Guía por módulo

Cada app tiene su propio `CLAUDE.md` con modelos, servicios, endpoints y flujos detallados:

| App | Sub-CLAUDE.md | Descripción |
|-----|---------------|-------------|
| `principal` | [principal/CLAUDE.md](erp_chvs/principal/CLAUDE.md) | Datos maestros, RBAC, audit logging, template tags |
| `nutricion` | [nutricion/CLAUDE.md](erp_chvs/nutricion/CLAUDE.md) | Menús, preparaciones, análisis nutricional, semaforización, match ICBF |
| `planeacion` | [planeacion/CLAUDE.md](erp_chvs/planeacion/CLAUDE.md) | Programas, raciones, ciclos de menús |
| `facturacion` | [facturacion/CLAUDE.md](erp_chvs/facturacion/CLAUDE.md) | Carga Excel PAE, PDFs de asistencia |
| `costos` | [costos/CLAUDE.md](erp_chvs/costos/CLAUDE.md) | Matriz de costos nutricionales, export Excel |
| `logistica` | [logistica/CLAUDE.md](erp_chvs/logistica/CLAUDE.md) | Rutas de entrega, asignación de sedes |
| `calidad` | [calidad/CLAUDE.md](erp_chvs/calidad/CLAUDE.md) | Certificados BPM, bot WhatsApp, PDF horizontal |
| `agente` | [agente/CLAUDE.md](erp_chvs/agente/CLAUDE.md) | Generador IA (Gemini), pool de borradores, RAG Pinecone |
| `contabilidad` | [contabilidad/CLAUDE.md](erp_chvs/contabilidad/CLAUDE.md) | Flujo multi-rol de facturas: Líder → Compras → Contabilidad |
| `dashboard` | [dashboard/CLAUDE.md](erp_chvs/dashboard/CLAUDE.md) | Punto de entrada post-login |

---

## Setup (desde `ERP_CHVS/`)

```bash
python -m venv .venv && source .venv/bin/activate
cd erp_chvs/
pip install -r requirements.txt
cp .env.example .env   # editar con credenciales
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver  # http://localhost:8000
```

## Comandos comunes (desde `erp_chvs/`)

```bash
# Servidor de desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations && python manage.py migrate

# Tests
python manage.py test                    # todos
python manage.py test nutricion.tests_guias_preparacion_excel --verbosity=2
# Con tests reales: nutricion, facturacion, principal
# Stubs vacíos: logistica, costos, planeacion, dashboard
DJANGO_SETTINGS_MODULE=erp_chvs.settings pytest -v

# Estáticos (producción)
python manage.py collectstatic

# Base de datos
python manage.py loaddata backup_utf8.json
python manage.py dbshell

# Comandos personalizados
python manage.py setup_groups          # Crea grupos RBAC por defecto
python manage.py optimizar_logos       # Optimiza logos de instituciones para PDFs
python manage.py inspeccionar_db       # Inspector de estructura de BD
python manage.py rellenar_pool         # Llena pool de borradores IA (min 20/modalidad)
python manage.py rellenar_pool --min 10 --modalidad "COMPLEMENTO PM"
python manage.py ingestar_normativo    # Ingesta normativos PAE a Pinecone (RAG)
python manage.py ingestar_normativo --archivo /ruta/archivo.json --dry-run
```

## Estructura del proyecto

```
ERP_CHVS/
├── erp_chvs/              # Raíz Django (todos los comandos se ejecutan aquí)
│   ├── erp_chvs/          # Settings, URLs, WSGI/ASGI
│   ├── principal/         # Datos maestros + RBAC
│   ├── nutricion/         # Planificación nutricional
│   ├── planeacion/        # Programas y raciones
│   ├── facturacion/       # Listas PAE Excel → PDF
│   ├── costos/            # Matriz de costos
│   ├── logistica/         # Rutas de entrega
│   ├── calidad/           # Certificados BPM + WhatsApp
│   ├── agente/            # Generador IA (Gemini)
│   ├── contabilidad/      # Flujo contable de facturas
│   ├── dashboard/         # Entrada post-login
│   ├── Api/               # [Planificado] Integración SIESA — stub vacío
│   ├── static/            # CSS/JS por módulo
│   └── templates/         # base.html + subdirectorios por app
├── archivos excel/        # Directorio de entrada/salida Excel
├── Procfile               # Config Railway
└── railway.toml           # Config deploy Railway
```

## Arquitectura general

**Lógica de negocio en `services.py` o `services/`, nunca en views.** Las vistas solo manejan HTTP request/response.

> **Excepción heredada** (no replicar): `costos/views.py`, `logistica/views.py` y `planeacion/views.py` (`ciclos_menus`) contienen lógica directamente en la vista.

**Stack frontend**: Bootstrap 5.3.3, SweetAlert2, jQuery, DataTables. AJAX con endpoints JSON, modales para formularios. HTML/CSS/JS siempre en archivos separados — sin estilos inline ni atributos `onclick`.

**Relaciones maestras**:
```
PrincipalDepartamento → PrincipalMunicipio → InstitucionesEducativas → SedesEducativas
                                ↓
                            Programa → PlanificacionRaciones → ListadosFocalizacion
```

## Autenticación y autorización

- Login → `/dashboard/`, logout → `/`
- RBAC via Django Groups (`principal.middleware.RoleAccessMiddleware`)
- Ver tabla completa de grupos y accesos en [principal/CLAUDE.md](erp_chvs/principal/CLAUDE.md)

## Configuración (`.env` en `erp_chvs/`)

```bash
DJANGO_SECRET_KEY=your-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos — prioridad: DATABASE_URL > DB_* > PG*
DB_NAME=erp_chvs
DB_USER=postgres
DB_PASSWORD=chvs2025
DB_HOST=localhost
DB_PORT=5432

GEMINI_API_KEY=your-key

# Agente — RAG via Pinecone (opcional; se desactiva silenciosamente si no se define)
# PINECONE_API_KEY=<key>
# PINECONE_INDEX=minutas-index
# PINECONE_NAMESPACE=minutas

# Calidad — WhatsApp bot
CALIDAD_WA_API_KEY=<compartida con ERP_API_KEY en servicio apiw>
EMPLEADOS_DB_URL=<URL PostgreSQL BD externa de empleados>

# Solo producción (Cloudinary para media):
# CLOUDINARY_CLOUD_NAME=  CLOUDINARY_API_KEY=  CLOUDINARY_API_SECRET=
```

**Localización**: `LANGUAGE_CODE = 'es-col'`, `TIME_ZONE = 'America/Bogota'`, `DECIMAL_SEPARATOR = '.'`

## Deployment (Railway)

- Config: `railway.toml` (Railway ignora `Procfile` cuando existe `railway.toml` — mantener ambos en sync)
- Secuencia de inicio: `migrate` → `collectstatic` → gunicorn (1 worker sync + 2 threads, timeout 600s)
- Static files: WhiteNoise (`WHITENOISE_USE_FINDERS = True`). **No usar** `CompressedStaticFilesStorage` (genera race condition con Python 3.13)
- Media: Cloudinary en producción (`DEBUG=False`)
- Python pinned en `runtime.txt`: `python-3.13.1`

**Variables Railway requeridas**:
```
DJANGO_SECRET_KEY, DJANGO_DEBUG=False, GEMINI_API_KEY
DATABASE_URL        (auto-set por Railway Postgres plugin)
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
CALIDAD_WA_API_KEY, EMPLEADOS_DB_URL
# Opcional RAG: PINECONE_API_KEY
```

## Convenciones

- **Español**: campos de modelo, lógica de negocio, comentarios, variables de dominio
- **Inglés**: definiciones de clases, código estructural Python/Django
- `bulk_create` para inserts masivos
- `"BUGA"` siempre se trata como alias de `"GUADALAJARA DE BUGA"`
- **Frontend performance**: `transition: propiedad-específica` (nunca `transition: all`), `DocumentFragment` para inserciones múltiples, `Promise.all()` para APIs paralelas

## Cloudinary y `FieldFile.path` en producción

En producción (`DEBUG=False`), `FieldFile.path` lanza `NotImplementedError` — Cloudinary no implementa `.path()`. Siempre capturar las tres excepciones:

```python
try:
    ruta = instancia.imagen.path
except (FileNotFoundError, ValueError, NotImplementedError):
    ruta = None
```

Archivos afectados: `nutricion/services/analisis_service.py` (bloque `logo_path` y función `_path_or_none`).

## Base de datos

- PostgreSQL, `CONN_MAX_AGE=600`, `CONN_HEALTH_CHECKS=True`
- Migraciones: directorios `migrations/` por app
- Backup: `python manage.py loaddata backup_utf8.json`

## Apps no activas

- `Api/` — integración SIESA planificada. Ver `planeacion/PROPUESTA_INTEGRACION_SIESA.md`
- `ocr_validation`, `iagenerativa` — eliminadas
