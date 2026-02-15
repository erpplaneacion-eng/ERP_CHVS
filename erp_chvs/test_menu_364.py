#!/usr/bin/env python
"""
Script de prueba específico para menú 364
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

print("=" * 70)
print("PRUEBA COMPLETA DEL MENÚ 364")
print("=" * 70)

# 1. Información básica del menú
menu = TablaMenus.objects.get(id_menu=364)
print(f"\n1️⃣ INFORMACIÓN DEL MENÚ")
print(f"  Menú: {menu.menu}")
print(f"  Modalidad: {menu.id_modalidad.modalidad}")
print(f"  Programa: {menu.id_contrato.programa if menu.id_contrato else 'N/A'}")

# 2. Preparaciones y componentes
preparaciones = TablaPreparaciones.objects.filter(id_menu=menu).prefetch_related(
    'ingredientes__id_ingrediente_siesa__id_componente'
)

print(f"\n2️⃣ PREPARACIONES ({preparaciones.count()})")
componentes_detectados = set()

for prep in preparaciones:
    print(f"\n  📌 {prep.preparacion}")

    # Componente de la preparación
    if prep.id_componente:
        componentes_detectados.add(prep.id_componente.id_componente)

    # Componentes de ingredientes
    for ing_rel in prep.ingredientes.all():
        alimento = ing_rel.id_ingrediente_siesa
        if alimento and alimento.id_componente:
            componentes_detectados.add(alimento.id_componente.id_componente)
            print(f"     - {alimento.nombre_del_alimento[:40]:40} → {alimento.id_componente.componente}")

print(f"\n3️⃣ COMPONENTES DETECTADOS EN EL MENÚ")
if componentes_detectados:
    from nutricion.models import ComponentesAlimentos
    for comp_id in sorted(componentes_detectados):
        comp = ComponentesAlimentos.objects.get(id_componente=comp_id)
        print(f"  ✅ {comp.componente}")
else:
    print("  ❌ No se detectaron componentes")

# 3. Requerimientos para esta modalidad
print(f"\n4️⃣ REQUERIMIENTOS PARA '{menu.id_modalidad.modalidad}'")
requerimientos = RequerimientoSemanal.objects.filter(
    modalidad=menu.id_modalidad
).select_related('componente')

if requerimientos.exists():
    print(f"  Total de requerimientos: {requerimientos.count()}")
    for req in requerimientos:
        tiene = '✅' if req.componente.id_componente in componentes_detectados else '❌'
        print(f"  {tiene} {req.componente.componente:30} → {req.frecuencia}x/semana")
else:
    print("  ❌ No hay requerimientos configurados para esta modalidad")

# 4. Simulación de validación semanal
print(f"\n5️⃣ SIMULACIÓN DE VALIDACIÓN SEMANAL")
print(f"  Si tuviéramos 5 menús como el 364 en una semana...")

menus_por_componente = {}
for comp_id in componentes_detectados:
    menus_por_componente[comp_id] = 1  # Solo 1 menú (el 364)

print("\n  Resultado:")
for req in requerimientos:
    comp_id = req.componente.id_componente
    actual = menus_por_componente.get(comp_id, 0)
    requerido = req.frecuencia
    cumple = actual >= requerido
    icono = '✅' if cumple else '❌'

    if actual > requerido:
        msg = f"(Excede por {actual - requerido})"
    elif actual < requerido:
        msg = f"(Falta {requerido - actual})"
    else:
        msg = "(Cumple exacto)"

    print(f"  {icono} {req.componente.componente:30} | {actual}/{requerido} {msg}")

# 5. Conclusión
print("\n" + "=" * 70)
print("CONCLUSIÓN")
print("=" * 70)

if componentes_detectados and requerimientos.exists():
    print("✅ El menú 364 TIENE componentes asignados")
    print("✅ La modalidad TIENE requerimientos configurados")
    print("✅ El sistema de validación PUEDE funcionar")
    print("\n⚠️  Para ver los validadores en la interfaz:")
    print("   1. Debe haber al menos 5 menús con preparaciones")
    print("   2. Los menús deben estar en la misma modalidad")
    print("   3. Hacer hard refresh del navegador (Ctrl+Shift+R)")
elif not componentes_detectados:
    print("❌ El menú 364 NO tiene componentes asignados")
else:
    print("⚠️  El menú tiene componentes pero la modalidad no tiene requerimientos")

print("=" * 70)
