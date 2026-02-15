#!/usr/bin/env python
"""
Verificación REAL de la validación semanal
Simula exactamente lo que hace el frontend
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.models import (
    TablaMenus,
    TablaPreparaciones,
    RequerimientoSemanal,
    ModalidadesDeConsumo
)
from planeacion.models import Programa
from collections import defaultdict

print("=" * 80)
print("VERIFICACIÓN REAL DE VALIDACIÓN SEMANAL")
print("Simulando el flujo EXACTO del frontend")
print("=" * 80)

# 1. Identificar el programa "programa alimentandonos 2025"
programa = Programa.objects.filter(programa__icontains='alimentandonos 2025').first()

if not programa:
    print("❌ No se encontró el programa 'programa alimentandonos 2025'")
    exit(1)

print(f"\n📋 PROGRAMA SELECCIONADO")
print("-" * 80)
print(f"ID: {programa.id}")
print(f"Nombre: {programa.programa}")
print(f"Contrato: {programa.contrato}")
print(f"Municipio: {programa.municipio}")

# 2. Buscar modalidad "ALMUERZO JORNADA UNICA"
modalidad = ModalidadesDeConsumo.objects.filter(
    modalidad__icontains='ALMUERZO JORNADA UNICA'
).first()

if not modalidad:
    print("❌ No se encontró la modalidad 'ALMUERZO JORNADA UNICA'")
    exit(1)

print(f"\n📋 MODALIDAD SELECCIONADA")
print("-" * 80)
print(f"ID: {modalidad.id_modalidades}")
print(f"Nombre: {modalidad.modalidad}")

# 3. Cargar menús EXACTAMENTE como lo hace el frontend
# Frontend: fetch(`/nutricion/api/menus/?programa_id=${programaId}`)
# Backend: menus_query.filter(id_contrato_id=programa_id)
print(f"\n🔍 CARGANDO MENÚS (como lo hace el frontend)")
print("-" * 80)
print(f"Query: TablaMenus.objects.filter(")
print(f"    id_contrato_id={programa.id},")
print(f"    id_modalidad_id={modalidad.id_modalidades}")
print(f").order_by('menu')")

menus = TablaMenus.objects.filter(
    id_contrato=programa,
    id_modalidad=modalidad
).order_by('menu')

print(f"\n✅ Menús encontrados: {menus.count()}")

if menus.count() == 0:
    print("❌ No hay menús para este programa y modalidad")
    exit(1)

# Mostrar todos los menús
print("\nListado completo de menús:")
for menu in menus:
    preps = TablaPreparaciones.objects.filter(id_menu=menu).count()
    print(f"  - Menú '{menu.menu}' (ID:{menu.id_menu}) | {preps} preparaciones")

# 4. Tomar los primeros 5 menús (Semana 1)
print(f"\n📊 SEMANA 1 (Menús 1-5)")
print("-" * 80)

menus_semana_1 = menus[:5]
menu_ids_semana_1 = [m.id_menu for m in menus_semana_1]

print(f"IDs de menús en Semana 1: {menu_ids_semana_1}")
print("\nDetalles:")
for menu in menus_semana_1:
    preps = TablaPreparaciones.objects.filter(id_menu=menu).count()
    print(f"  - Menú '{menu.menu}' (ID:{menu.id_menu}) | {preps} preparaciones")

# 5. Ejecutar la lógica EXACTA de validación del backend
print(f"\n🔍 VALIDACIÓN SEMANAL")
print("=" * 80)

# Contar componentes (lógica exacta del backend)
menus_por_componente = {}

for menu_id in menu_ids_semana_1:
    preparaciones = TablaPreparaciones.objects.filter(
        id_menu_id=menu_id
    ).prefetch_related('ingredientes__id_ingrediente_siesa__id_componente')

    componentes_del_menu = set()

    for prep in preparaciones:
        # 1. Componente de la preparación
        if prep.id_componente:
            componentes_del_menu.add(prep.id_componente.id_componente)

        # 2. Componentes de ingredientes
        for ingrediente_rel in prep.ingredientes.all():
            alimento = ingrediente_rel.id_ingrediente_siesa
            if alimento and alimento.id_componente:
                componentes_del_menu.add(alimento.id_componente.id_componente)

    for comp_id in componentes_del_menu:
        if comp_id not in menus_por_componente:
            menus_por_componente[comp_id] = set()
        menus_por_componente[comp_id].add(menu_id)

conteo_componentes = {
    comp_id: len(menus_set)
    for comp_id, menus_set in menus_por_componente.items()
}

# Comparar con requerimientos
requerimientos = RequerimientoSemanal.objects.filter(
    modalidad=modalidad
).select_related('componente').order_by('componente__componente')

print("\nRESULTADO DE LA VALIDACIÓN (lo que REALMENTE ve el usuario):")
print("-" * 80)

cumple_total = True
for req in requerimientos:
    comp_id = req.componente.id_componente
    comp_nombre = req.componente.componente
    requerido = req.frecuencia
    actual = conteo_componentes.get(comp_id, 0)
    cumple = actual >= requerido

    if not cumple:
        cumple_total = False

    icono = '✅' if cumple else '❌'

    if actual > requerido:
        mensaje = f"(Excede por {actual - requerido})"
    elif actual < requerido:
        mensaje = f"(Falta {requerido - actual})"
    else:
        mensaje = "(Cumple exacto)"

    print(f"{icono} {comp_nombre:40} {actual} / {requerido} {mensaje}")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)
print(f"Programa: {programa.programa}")
print(f"Modalidad: {modalidad.modalidad}")
print(f"Menús en Semana 1: {menu_ids_semana_1}")
print(f"Cumplimiento total: {'✅ SÍ' if cumple_total else '❌ NO'}")

print("\n💡 CÓMO VERIFICAR EN LA INTERFAZ:")
print("-" * 80)
print("1. Ir a: http://127.0.0.1:8000/nutricion/menus/")
print(f"2. Seleccionar programa: {programa.programa}")
print(f"3. Expandir modalidad: {modalidad.modalidad}")
print("4. Ver sección 'Semana 1'")
print("5. El validador debajo de las tarjetas debe mostrar los mismos resultados")
print("\n⚠️  Si NO coincide:")
print("   - Hacer hard refresh: Ctrl+Shift+R")
print("   - Verificar consola del navegador (F12) por errores")
print("   - Verificar que los IDs de menús en la API coincidan")

print("\n" + "=" * 80)
