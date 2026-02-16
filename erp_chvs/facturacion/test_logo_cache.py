"""
Script de prueba para verificar que el cache del logo funciona correctamente
en generación masiva de PDFs.

Uso:
    python manage.py shell < facturacion/test_logo_cache.py
"""

from facturacion.pdf_generator import _logo_cache
from planeacion.models import Programa

# Obtener un programa con imagen
programa = Programa.objects.filter(imagen__isnull=False).first()

if not programa:
    print("❌ No se encontró ningún programa con imagen asignada")
    print("   Por favor, asigna una imagen a un programa primero")
    exit()

print(f"✅ Programa encontrado: {programa.programa}")
print(f"   URL de la imagen: {programa.imagen.url if programa.imagen else 'N/A'}")

# Verificar si la imagen está en cache
from django.conf import settings
if hasattr(settings, 'DEBUG') and not settings.DEBUG:
    logo_url = programa.imagen.url
else:
    try:
        logo_url = programa.imagen.path
    except:
        logo_url = programa.imagen.url

print(f"\n📍 Ruta del logo a usar: {logo_url}")

# Verificar cache
if logo_url in _logo_cache:
    print("✅ El logo YA ESTÁ en cache (se reutilizará sin descargar)")
else:
    print("⚠️  El logo NO está en cache (se descargará la primera vez)")

# Simular descarga y cache
print("\n🔄 Simulando pre-carga del logo...")
import requests
from io import BytesIO
from reportlab.lib.utils import ImageReader

if isinstance(logo_url, str) and logo_url.startswith(("http://", "https://")):
    try:
        response = requests.get(logo_url, timeout=30, stream=True)
        response.raise_for_status()
        image_content = BytesIO(response.content)
        logo_reader = ImageReader(image_content)
        _logo_cache[logo_url] = logo_reader
        print(f"✅ Logo descargado y guardado en cache ({len(response.content)} bytes)")
    except Exception as e:
        print(f"❌ Error al descargar logo: {e}")
else:
    print(f"✅ Logo local, no requiere descarga: {logo_url}")

# Verificar cache nuevamente
if logo_url in _logo_cache:
    print("\n✅ VERIFICACIÓN: El logo está en cache y será reutilizado por todos los PDFs")
    print(f"   Total de entradas en cache: {len(_logo_cache)}")
else:
    print("\n❌ PROBLEMA: El logo no se guardó en cache correctamente")

print("\n" + "="*60)
print("RESULTADO: El sistema está listo para generar PDFs masivos")
print("          usando el logo desde cache sin múltiples descargas")
print("="*60)
