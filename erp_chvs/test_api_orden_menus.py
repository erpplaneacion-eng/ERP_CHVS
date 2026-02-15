#!/usr/bin/env python
"""
Test para verificar que la API retorna menús en orden numérico correcto
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from django.test import Client
from planeacion.models import Programa

print("=" * 80)
print("TEST: Orden numérico de menús en la API")
print("=" * 80)

# Obtener ID del programa
programa = Programa.objects.filter(programa__icontains='alimentandonos 2025').first()

if not programa:
    print("❌ Programa no encontrado")
    exit(1)

print(f"\n📋 Programa: {programa.programa} (ID: {programa.id})")

# Crear cliente para hacer requests
client = Client()

# Login como usuario (necesario para @login_required)
from django.contrib.auth.models import User
user = User.objects.first()
if not user:
    print("❌ No hay usuarios en la BD")
    exit(1)

client.force_login(user)

# Hacer request a la API
url = f'/nutricion/api/menus/?programa_id={programa.id}'
print(f"\n🔍 Haciendo request a: {url}")

response = client.get(url)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    print(response.content)
    exit(1)

data = response.json()
menus = data.get('menus', [])

print(f"\n✅ Respuesta exitosa: {len(menus)} menús")

# Filtrar menús de ALMUERZO JORNADA UNICA
menus_almuerzo = [m for m in menus if 'ALMUERZO JORNADA UNICA' in m['id_modalidad__modalidad']]

print(f"\n📊 Menús de ALMUERZO JORNADA UNICA: {len(menus_almuerzo)}")
print("\nOrden en que llegan del backend:")
print("-" * 80)

for i, menu in enumerate(menus_almuerzo[:10], 1):
    print(f"{i:2d}. Menú '{menu['menu']}' (ID:{menu['id_menu']})")

# Verificar si los primeros 5 son 1, 2, 3, 4, 5
primeros_5 = [m['menu'] for m in menus_almuerzo[:5]]
esperado = ['1', '2', '3', '4', '5']

print(f"\n🔍 VERIFICACIÓN")
print("-" * 80)
print(f"Primeros 5 menús: {primeros_5}")
print(f"Esperado:         {esperado}")

if primeros_5 == esperado:
    print("\n✅ ¡CORRECTO! Los menús llegan en orden numérico")
    print("\nLos primeros 5 IDs (Semana 1):")
    semana_1_ids = [m['id_menu'] for m in menus_almuerzo[:5]]
    print(semana_1_ids)
    print("\nEstos son los menús que se validarán en la interfaz")
else:
    print("\n❌ ERROR: Los menús NO están en orden numérico")
    print("El backend aún está ordenando alfabéticamente")

print("\n" + "=" * 80)
