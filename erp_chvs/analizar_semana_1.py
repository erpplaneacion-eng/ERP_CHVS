#!/usr/bin/env python
"""
Análisis de Semana 1 - Menús 364-368
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.models import (
    TablaMenus,
    TablaPreparaciones,
    RequerimientoSemanal,
    ComponentesAlimentos
)
from collections import defaultdict

print("=" * 80)
print("ANÁLISIS DE VALIDACIÓN SEMANAL - SEMANA 1")
print("Menús: 364, 365, 366, 367, 368")
print("=" * 80)

# IDs de los menús de la semana 1
menu_ids = [364, 365, 366, 367, 368]

# Obtener información básica
print("\n📋 INFORMACIÓN DE LOS MENÚS")
print("-" * 80)

menus = TablaMenus.objects.filter(id_menu__in=menu_ids).order_by('id_menu')

if not menus.exists():
    print("❌ No se encontraron los menús especificados")
    exit(1)

modalidad = menus.first().id_modalidad
print(f"Modalidad: {modalidad.modalidad}")
print(f"Total de menús: {menus.count()}")

for menu in menus:
    preps = TablaPreparaciones.objects.filter(id_menu=menu).count()
    print(f"  - Menú {menu.menu} (ID:{menu.id_menu}): {preps} preparaciones")

# Contar componentes por menú (como lo hace el backend)
print("\n🔍 ANÁLISIS DE COMPONENTES POR MENÚ")
print("-" * 80)

menus_por_componente = defaultdict(set)

for menu in menus:
    print(f"\n📌 Menú {menu.menu} (ID:{menu.id_menu})")

    preparaciones = TablaPreparaciones.objects.filter(
        id_menu=menu
    ).prefetch_related('ingredientes__id_ingrediente_siesa__id_componente')

    componentes_del_menu = set()

    for prep in preparaciones:
        print(f"   └─ {prep.preparacion}")

        # 1. Componente de la preparación (si existe)
        if prep.id_componente:
            componentes_del_menu.add(prep.id_componente.id_componente)
            print(f"      → Componente prep: {prep.id_componente.componente}")

        # 2. Componentes de los ingredientes
        for ing_rel in prep.ingredientes.all():
            alimento = ing_rel.id_ingrediente_siesa
            if alimento and alimento.id_componente:
                componentes_del_menu.add(alimento.id_componente.id_componente)
                print(f"      → {alimento.nombre_del_alimento[:35]:35} | {alimento.id_componente.componente}")

    # Registrar componentes únicos de este menú
    for comp_id in componentes_del_menu:
        menus_por_componente[comp_id].add(menu.id_menu)

    print(f"   ✓ Componentes únicos en este menú: {len(componentes_del_menu)}")

# Calcular conteo de componentes
conteo_componentes = {
    comp_id: len(menus_set)
    for comp_id, menus_set in menus_por_componente.items()
}

# Obtener requerimientos para esta modalidad
requerimientos = RequerimientoSemanal.objects.filter(
    modalidad=modalidad
).select_related('componente').order_by('componente__componente')

print("\n📊 VALIDACIÓN SEMANAL")
print("=" * 80)

if not requerimientos.exists():
    print("❌ No hay requerimientos configurados para esta modalidad")
    exit(1)

print(f"Requerimientos configurados: {requerimientos.count()}\n")

cumple_total = True
resultados = []

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

    resultados.append({
        'icono': icono,
        'componente': comp_nombre,
        'actual': actual,
        'requerido': requerido,
        'cumple': cumple,
        'mensaje': mensaje
    })

    print(f"{icono} {comp_nombre:35} | {actual}/{requerido} {mensaje}")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)
print(f"Cumplimiento total: {'✅ SÍ' if cumple_total else '❌ NO'}")
print(f"Componentes que cumplen: {sum(1 for r in resultados if r['cumple'])}/{len(resultados)}")

# Componentes detectados pero no requeridos
componentes_detectados_ids = set(conteo_componentes.keys())
componentes_requeridos_ids = set(req.componente.id_componente for req in requerimientos)
componentes_extra = componentes_detectados_ids - componentes_requeridos_ids

if componentes_extra:
    print(f"\n⚠️  Componentes detectados NO requeridos:")
    for comp_id in componentes_extra:
        comp = ComponentesAlimentos.objects.get(id_componente=comp_id)
        print(f"   • {comp.componente} (aparece {conteo_componentes[comp_id]}x)")

# Mostrar cómo se vería en la interfaz
print("\n" + "=" * 80)
print("VISTA PREVIA DE LA INTERFAZ")
print("=" * 80)
print("""
┌────────────────────────────────────────────────────────────┐
│ 📊 Validación Semanal - Semana 1                          │
├────────────────────────────────────────────────────────────┤""")

for r in resultados:
    padding = ' ' * (35 - len(r['componente']))
    print(f"│ {r['icono']} {r['componente']}{padding} {r['actual']}/{r['requerido']} {r['mensaje']:20} │")

print("""└────────────────────────────────────────────────────────────┘
""")

print("\n💡 CÓMO VER ESTO EN LA INTERFAZ:")
print("-" * 80)
print("1. Ir a: http://127.0.0.1:8000/nutricion/menus/")
print(f"2. Seleccionar programa y modalidad: {modalidad.modalidad}")
print("3. Expandir el acordeón de la modalidad")
print("4. Buscar la sección 'Semana 1'")
print("5. Debajo de las tarjetas de menús 1-5, aparecerá el validador")
print("\n⚠️  Si NO aparece:")
print("   - Hacer hard refresh: Ctrl+Shift+R (Windows/Linux) o Cmd+Shift+R (Mac)")
print("   - Verificar consola del navegador (F12) por errores JavaScript")
print("   - Verificar que la URL de la API responde:")
print(f"     /nutricion/api/validar-semana/?menu_ids={','.join(map(str, menu_ids))}&modalidad_id={modalidad.id_modalidades}")

print("\n" + "=" * 80)
