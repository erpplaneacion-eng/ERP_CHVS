#!/usr/bin/env python
"""
Test del orden numérico en el query
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from django.db.models import Case, IntegerField, Value, When
from django.db.models.functions import Cast
from nutricion.models import TablaMenus
from planeacion.models import Programa

print("=" * 80)
print("TEST: Orden numérico con annotate + Cast")
print("=" * 80)

# Obtener el programa
programa = Programa.objects.filter(programa__icontains='alimentandonos 2025').first()

if not programa:
    print("❌ Programa no encontrado")
    exit(1)

print(f"\n📋 Programa: {programa.programa} (ID: {programa.id})")

# Buscar modalidad ALMUERZO JORNADA UNICA
from nutricion.models import ModalidadesDeConsumo
modalidad = ModalidadesDeConsumo.objects.filter(
    modalidad__icontains='ALMUERZO JORNADA UNICA'
).first()

if not modalidad:
    print("❌ Modalidad no encontrada")
    exit(1)

print(f"📋 Modalidad: {modalidad.modalidad} (ID: {modalidad.id_modalidades})")

print("\n" + "=" * 80)
print("ANTES: Orden alfabético (order_by('menu'))")
print("=" * 80)

menus_alfabetico = TablaMenus.objects.filter(
    id_contrato=programa,
    id_modalidad=modalidad
).order_by('menu')

print("\nPrimeros 10 menús con orden alfabético:")
for i, menu in enumerate(menus_alfabetico[:10], 1):
    print(f"{i:2d}. Menú '{menu.menu}' (ID:{menu.id_menu})")

primeros_5_alf = [m.menu for m in menus_alfabetico[:5]]
print(f"\nPrimeros 5: {primeros_5_alf}")

print("\n" + "=" * 80)
print("DESPUÉS: Orden numérico (annotate + Cast)")
print("=" * 80)

menus_numerico = TablaMenus.objects.filter(
    id_contrato=programa,
    id_modalidad=modalidad
).annotate(
    menu_numerico=Case(
        When(menu__regex=r'^\d+$', then=Cast('menu', IntegerField())),
        default=Value(9999),
        output_field=IntegerField()
    )
).order_by('menu_numerico')

print("\nPrimeros 10 menús con orden numérico:")
for i, menu in enumerate(menus_numerico[:10], 1):
    # Mostrar también el valor de menu_numerico si existe
    num_val = getattr(menu, 'menu_numerico', 'N/A')
    print(f"{i:2d}. Menú '{menu.menu}' (ID:{menu.id_menu}, num={num_val})")

primeros_5_num = [m.menu for m in menus_numerico[:5]]
print(f"\nPrimeros 5: {primeros_5_num}")

print("\n" + "=" * 80)
print("VERIFICACIÓN")
print("=" * 80)

esperado = ['1', '2', '3', '4', '5']
print(f"Esperado:   {esperado}")
print(f"Alfabético: {primeros_5_alf}")
print(f"Numérico:   {primeros_5_num}")

if primeros_5_num == esperado:
    print("\n✅ ¡CORRECTO! El orden numérico funciona")
    semana_1_ids = [m.id_menu for m in menus_numerico[:5]]
    print(f"\nIDs de Semana 1: {semana_1_ids}")
    print("Estos son los menús correctos para la validación semanal")
else:
    print("\n❌ ERROR: El orden numérico NO funciona como esperado")

print("\n" + "=" * 80)
