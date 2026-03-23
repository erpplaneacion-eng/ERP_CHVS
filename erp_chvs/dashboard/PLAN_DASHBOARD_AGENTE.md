# Plan: Dashboard Agéntico — Feed de Actividad con Resumen IA

## Contexto y motivación

El dashboard actual (`/dashboard/`) es una vista vacía que solo muestra accesos directos por rol. El objetivo es transformarlo en un **feed de noticias del sistema** que reemplace los gráficos estáticos por información viva: cuántos menús generó la IA, cuántas focalizaciones cambiaron, qué PDFs se produjeron, y un resumen ejecutivo generado por IA cada hora.

La infraestructura necesaria ya existe:
- `RegistroActividad` (en `principal/models.py`) — todas las apps ya escriben aquí
- Gemini API — ya configurada en la app `agente/`
- Django cache framework — disponible en el proyecto

---

## Arquitectura propuesta (2 capas)

### Capa 1 — Feed de actividad (sin costo, sin IA)
Query directa a `RegistroActividad`. Muestra las últimas 50 acciones en tiempo real via AJAX polling.

### Capa 2 — Briefing diario IA (Gemini, cacheado 1h)
Resumen en lenguaje natural generado una vez por hora. Describe patrones, alertas y tendencias.

---

## Archivos a crear / modificar

| Archivo | Tipo | Cambio |
|---------|------|--------|
| `dashboard/views.py` | Modificar | Vista principal + 2 endpoints JSON |
| `dashboard/services.py` | **Nuevo** | Lógica de consulta + prompt Gemini |
| `dashboard/urls.py` | **Nuevo** | Registrar endpoints |
| `templates/dashboard/dashboard.html` | Modificar | Layout con feed + briefing + KPIs |
| `static/js/dashboard/dashboard.js` | **Nuevo** | Polling y render del feed |
| `static/css/dashboard/dashboard.css` | **Nuevo** | Estilos del feed |

**Sin migraciones** — no se crean nuevos modelos.

---

## Implementación detallada

### `dashboard/services.py` (nuevo)

```python
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from django.db.models import Count
from principal.models import RegistroActividad
import google.generativeai as genai
import os

CACHE_KEY_BRIEFING = 'dashboard_briefing_ia'
CACHE_TTL = 3600  # 1 hora


def obtener_feed_actividad(limite=50):
    return (
        RegistroActividad.objects
        .select_related('usuario')
        .order_by('-fecha')[:limite]
    )


def obtener_resumen_24h():
    desde = timezone.now() - timedelta(hours=24)
    return (
        RegistroActividad.objects
        .filter(fecha__gte=desde)
        .values('modulo', 'exitoso')
        .annotate(total=Count('id'))
        .order_by('modulo')
    )


def obtener_briefing_ia():
    """Genera o recupera del cache el briefing diario de Gemini."""
    cached = cache.get(CACHE_KEY_BRIEFING)
    if cached:
        return cached

    resumen = obtener_resumen_24h()
    if not resumen:
        return "Sin actividad registrada en las últimas 24 horas."

    # Construir prompt con datos reales
    lineas = []
    for item in resumen:
        estado = "exitosos" if item['exitoso'] else "con error"
        lineas.append(f"- {item['modulo']}: {item['total']} acciones {estado}")

    prompt = (
        "Eres el asistente del ERP PAE Colombia. "
        "Resume en máximo 3 frases cortas y ejecutivas la actividad del sistema "
        "en las últimas 24 horas. Menciona anomalías si hay errores. "
        "Datos:\n" + "\n".join(lineas)
    )

    genai.configure(api_key=os.environ.get('GEMINI_API_KEY', ''))
    model = genai.GenerativeModel('gemini-1.5-flash')
    respuesta = model.generate_content(prompt)
    texto = respuesta.text.strip()

    cache.set(CACHE_KEY_BRIEFING, texto, CACHE_TTL)
    return texto
```

### `dashboard/views.py`

```python
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from . import services


@login_required
def dashboard_view(request):
    resumen = services.obtener_resumen_24h()
    return render(request, 'dashboard/dashboard.html', {'resumen_24h': list(resumen)})


@login_required
def api_feed(request):
    actividades = services.obtener_feed_actividad()
    data = [
        {
            'modulo': a.modulo,
            'accion': a.accion,
            'descripcion': a.descripcion,
            'usuario': a.usuario.get_full_name() or a.usuario.username if a.usuario else 'Sistema',
            'fecha': a.fecha.strftime('%d/%m/%Y %H:%M'),
            'exitoso': a.exitoso,
        }
        for a in actividades
    ]
    return JsonResponse({'actividades': data})


@login_required
def api_briefing(request):
    try:
        texto = services.obtener_briefing_ia()
        return JsonResponse({'briefing': texto, 'ok': True})
    except Exception as e:
        return JsonResponse({'briefing': 'No disponible en este momento.', 'ok': False})
```

### `dashboard/urls.py` (nuevo)

```python
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('api/feed/', views.api_feed, name='api_feed'),
    path('api/briefing/', views.api_briefing, name='api_briefing'),
]
```

### Layout del template `dashboard.html`

```
┌─────────────────────────────────────────────────────┐
│  🤖  Briefing IA del día  (card superior)           │
│  "Hoy se cargaron 3 focalizaciones con 1,240        │
│   beneficiarios. La IA generó 8 preparaciones.      │
│   Sin errores registrados."                         │
├────────────────────┬────────────────────────────────┤
│  KPIs 24h          │  Feed de actividad (scroll)    │
│  • Facturación: 5  │  🟢 14:32 — María García       │
│  • Nutrición: 12   │       Focalizaciones guardadas  │
│  • Agente IA: 8    │       1,240 registros           │
│  • Errores: 0      │  🟢 14:15 — Juan López          │
│                    │       PDF masivo generado        │
│                    │  🔴 13:50 — Error cargue Excel  │
└────────────────────┴────────────────────────────────┘
│  Accesos directos por rol (sección existente)       │
└─────────────────────────────────────────────────────┘
```

### Mapeo de íconos por acción (en JS)

```javascript
const ICONOS_ACCIONES = {
    guardar_listados:       { icon: 'bi-people-fill',      label: 'Focalizaciones guardadas' },
    cargue_excel:           { icon: 'bi-file-earmark-excel', label: 'Cargue Excel' },
    generar_pdf:            { icon: 'bi-file-pdf',          label: 'PDF generado' },
    generar_zip_masivo:     { icon: 'bi-archive',           label: 'ZIP masivo generado' },
    reemplazar_focalizacion:{ icon: 'bi-arrow-repeat',      label: 'Focalizaciones reemplazadas' },
    generar_menus_automaticos: { icon: 'bi-calendar2-week', label: 'Menús generados' },
    copiar_modalidad:       { icon: 'bi-copy',              label: 'Modalidad copiada' },
    crear_preparacion:      { icon: 'bi-robot',             label: 'Preparación IA creada' },
};

const ICONOS_MODULOS = {
    agente:      'bi-robot',
    facturacion: 'bi-receipt',
    nutricion:   'bi-egg-fried',
    planeacion:  'bi-calendar3',
    contabilidad:'bi-calculator',
    principal:   'bi-building',
};
```

---

## Reglas de arquitectura

- Lógica de negocio y llamada a Gemini → `dashboard/services.py`
- Views solo manejan HTTP → llaman al service
- Sin `onclick` inline, sin estilos inline
- JS en `static/js/dashboard/dashboard.js`
- Polling cada 60 segundos con `setInterval`
- Briefing IA: solo se llama a Gemini si el cache expiró (1 hora)

---

## Verificación post-implementación

1. `GET /dashboard/` → se ve el feed con actividades reales de la BD
2. `GET /dashboard/api/feed/` → devuelve JSON con últimas 50 actividades
3. `GET /dashboard/api/briefing/` → devuelve texto generado por Gemini
4. Segunda llamada a `/dashboard/api/briefing/` (< 1h) → responde sin llamar Gemini (cache)
5. Actividad con `exitoso=False` → aparece en rojo en el feed
6. Con `GEMINI_API_KEY` ausente → el briefing muestra mensaje graceful, no rompe la página

---

## Prioridad de implementación

| Fase | Componente | Valor |
|------|------------|-------|
| 1 | Feed de actividad + KPIs 24h | Alto — datos reales, sin riesgo |
| 2 | Briefing IA con Gemini + cache | Alto — diferenciador agéntico |
| 3 | Polling JS automático (60s) | Medio — mejora UX |
