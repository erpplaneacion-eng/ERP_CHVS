#!/usr/bin/env python
"""
Debug de la API de validación - Comparar con lo que muestra la interfaz
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.models import (
    TablaMenus,
    TablaPreparaciones,
    RequerimientoSemanal
)
from collections import defaultdict

print("=" * 80)
print("DEBUG: ¿Por qué la interfaz muestra datos diferentes?")
print("=" * 80)

# IDs que deberían estar en la semana 1
menu_ids_esperados = [364, 365, 366, 367, 368]

print("\n1️⃣ VERIFICAR MENÚS ESPERADOS")
print("-" * 80)

for menu_id in menu_ids_esperados:
    try:
        menu = TablaMenus.objects.get(id_menu=menu_id)
        preps = TablaPreparaciones.objects.filter(id_menu=menu).count()
        print(f"Menú ID {menu_id} | Número: '{menu.menu}' | Modalidad: {menu.id_modalidad.modalidad} | Preps: {preps}")
    except TablaMenus.DoesNotExist:
        print(f"Menú ID {menu_id} | ❌ NO EXISTE")

print("\n2️⃣ BUSCAR TODOS LOS MENÚS NUMERADOS 1-5 DE ALMUERZO JORNADA UNICA")
print("-" * 80)

from nutricion.models import ModalidadesDeConsumo

# Buscar la modalidad
modalidad_almuerzo = ModalidadesDeConsumo.objects.filter(
    modalidad__icontains='ALMUERZO JORNADA UNICA'
).first()

if modalidad_almuerzo:
    print(f"Modalidad encontrada: {modalidad_almuerzo.modalidad} (ID:{modalidad_almuerzo.id_modalidades})")

    # Buscar menús con números 1-5
    for num in ['1', '2', '3', '4', '5']:
        menus = TablaMenus.objects.filter(
            id_modalidad=modalidad_almuerzo,
            menu=num
        )

        if menus.exists():
            print(f"\nMenús con número '{num}':")
            for menu in menus:
                preps = TablaPreparaciones.objects.filter(id_menu=menu).count()
                programa = menu.id_contrato.programa if menu.id_contrato else 'Sin programa'
                print(f"  - ID:{menu.id_menu} | Programa: {programa} | Preparaciones: {preps}")
        else:
            print(f"\nMenús con número '{num}': ❌ No existen")

print("\n3️⃣ SIMULACIÓN DE LA LÓGICA DEL FRONTEND")
print("-" * 80)
print("El frontend debería:")
print("1. Filtrar menús por modalidad")
print("2. Tomar los primeros 5 menús ordenados (menús 1-5)")
print("3. Obtener sus IDs")
print("4. Llamar a la API con esos IDs")

# Simular lo que hace el frontend
if modalidad_almuerzo:
    menus_modalidad = TablaMenus.objects.filter(
        id_modalidad=modalidad_almuerzo
    ).order_by('menu')[:5]

    menu_ids_frontend = [m.id_menu for m in menus_modalidad]

    print(f"\nIDs que el frontend enviaría: {menu_ids_frontend}")
    print(f"IDs que esperábamos: {menu_ids_esperados}")

    if menu_ids_frontend != menu_ids_esperados:
        print("\n⚠️  ¡PROBLEMA DETECTADO! Los IDs no coinciden")
        print("\nDetalles de los menús que el frontend está tomando:")
        for i, menu in enumerate(menus_modalidad, 1):
            preps = TablaPreparaciones.objects.filter(id_menu=menu).count()
            programa = menu.id_contrato.programa if menu.id_contrato else 'Sin programa'
            print(f"{i}. Menú '{menu.menu}' (ID:{menu.id_menu}) | {programa} | {preps} preps")

print("\n4️⃣ EJECUTAR LA LÓGICA EXACTA DE LA API")
print("-" * 80)

# Usar los IDs que probablemente está usando el frontend
if modalidad_almuerzo:
    # Obtener los primeros 5 menús de esta modalidad
    menus_reales = TablaMenus.objects.filter(
        id_modalidad=modalidad_almuerzo
    ).order_by('menu')[:5]

    menu_ids_reales = [m.id_menu for m in menus_reales]

    print(f"Analizando menús: {menu_ids_reales}\n")

    # Contar componentes (lógica exacta del backend)
    menus_por_componente = {}

    for menu_id in menu_ids_reales:
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
        modalidad=modalidad_almuerzo
    ).select_related('componente').order_by('componente__componente')

    print("RESULTADO DE LA API (lo que debería ver en la interfaz):")
    print("-" * 80)

    for req in requerimientos:
        comp_id = req.componente.id_componente
        comp_nombre = req.componente.componente
        requerido = req.frecuencia
        actual = conteo_componentes.get(comp_id, 0)
        cumple = actual >= requerido

        icono = '✅' if cumple else '❌'

        if actual > requerido:
            mensaje = f"(Excede por {actual - requerido})"
        elif actual < requerido:
            mensaje = f"(Falta {requerido - actual})"
        else:
            mensaje = "(Cumple exacto)"

        print(f"{icono} {comp_nombre:40} {actual} / {requerido} {mensaje}")

print("\n5️⃣ VERIFICAR PREPARACIONES E INGREDIENTES DE CADA MENÚ")
print("-" * 80)

if modalidad_almuerzo:
    for menu in menus_reales:
        print(f"\n📌 Menú '{menu.menu}' (ID:{menu.id_menu})")

        preparaciones = TablaPreparaciones.objects.filter(
            id_menu=menu
        ).prefetch_related('ingredientes__id_ingrediente_siesa__id_componente')

        if not preparaciones.exists():
            print("   ❌ Sin preparaciones")
            continue

        for prep in preparaciones:
            print(f"   └─ {prep.preparacion}")

            # Verificar si tiene ingredientes
            ingredientes = prep.ingredientes.all()
            if not ingredientes.exists():
                print(f"      ⚠️  Sin ingredientes asignados")
            else:
                for ing_rel in ingredientes:
                    alimento = ing_rel.id_ingrediente_siesa
                    if alimento:
                        comp = alimento.id_componente.componente if alimento.id_componente else "SIN COMPONENTE"
                        print(f"      • {alimento.nombre_del_alimento[:40]:40} → {comp}")

print("\n" + "=" * 80)
print("CONCLUSIÓN")
print("=" * 80)
print("Compara los resultados de la sección 4 con lo que ves en la interfaz.")
print("Si coinciden, entonces la API está funcionando correctamente pero")
print("puede haber un problema de cache o los datos cambiaron.")
print("\nSi NO coinciden, hay un bug en la lógica de la API.")
print("=" * 80)
