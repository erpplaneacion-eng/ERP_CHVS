#!/usr/bin/env python
"""
Script de diagnóstico para validación semanal
Ejecutar: python manage.py shell < diagnostico_validacion.py
"""

from nutricion.models import (
    RequerimientoSemanal,
    TablaMenus,
    TablaPreparaciones,
    TablaAlimentos2018Icbf,
    ModalidadesDeConsumo,
    ComponentesAlimentos
)

print("=" * 60)
print("DIAGNÓSTICO: SISTEMA DE VALIDACIÓN SEMANAL")
print("=" * 60)

# 1. Requerimientos Semanales
print("\n1. REQUERIMIENTOS SEMANALES")
print("-" * 60)
total_reqs = RequerimientoSemanal.objects.count()
print(f"✓ Total requerimientos en BD: {total_reqs}")

if total_reqs == 0:
    print("❌ ERROR: No hay requerimientos semanales configurados")
    print("   Solución: Ejecutar migración 0004_requerimiento_semanal.py")
else:
    modalidades_con_reqs = RequerimientoSemanal.objects.values('modalidad__modalidad').distinct().count()
    print(f"✓ Modalidades con requerimientos: {modalidades_con_reqs}")

    # Mostrar muestra
    print("\nEjemplos de requerimientos:")
    for req in RequerimientoSemanal.objects.select_related('modalidad', 'componente')[:5]:
        print(f"  - {req.modalidad.modalidad}: {req.componente.componente} = {req.frecuencia}x/semana")

# 2. Componentes en Ingredientes
print("\n2. COMPONENTES EN INGREDIENTES")
print("-" * 60)
total_ingredientes = TablaAlimentos2018Icbf.objects.count()
con_componente = TablaAlimentos2018Icbf.objects.filter(id_componente__isnull=False).count()
sin_componente = TablaAlimentos2018Icbf.objects.filter(id_componente__isnull=True).count()

print(f"✓ Total ingredientes ICBF: {total_ingredientes}")
print(f"✓ Con componente asignado: {con_componente} ({con_componente/total_ingredientes*100:.1f}%)")
print(f"{'✓' if sin_componente == 0 else '❌'} Sin componente: {sin_componente}")

if sin_componente > 0:
    print("\n  Ingredientes sin componente:")
    for ing in TablaAlimentos2018Icbf.objects.filter(id_componente__isnull=True)[:10]:
        print(f"    - {ing.codigo}: {ing.nombre_del_alimento}")

# 3. Menús y Preparaciones
print("\n3. MENÚS Y PREPARACIONES")
print("-" * 60)
total_menus = TablaMenus.objects.count()
print(f"✓ Total menús creados: {total_menus}")

menus_con_prep = TablaMenus.objects.filter(
    id_menu__in=TablaPreparaciones.objects.values('id_menu')
).distinct().count()
print(f"✓ Menús con preparaciones: {menus_con_prep}")

if total_menus > 0:
    modalidades = TablaMenus.objects.values('id_modalidad__modalidad').distinct()
    print(f"\nModalidades con menús creados:")
    for mod in modalidades:
        count = TablaMenus.objects.filter(id_modalidad__modalidad=mod['id_modalidad__modalidad']).count()
        print(f"  - {mod['id_modalidad__modalidad']}: {count} menús")

# 4. Verificación de Semana Ejemplo
print("\n4. VERIFICACIÓN SEMANA EJEMPLO (Menús 1-5)")
print("-" * 60)
menus_semana_1 = TablaMenus.objects.filter(menu__in=['1', '2', '3', '4', '5']).order_by('menu')

if menus_semana_1.exists():
    print(f"✓ Menús encontrados: {menus_semana_1.count()}")

    for menu in menus_semana_1:
        preps = TablaPreparaciones.objects.filter(id_menu=menu).count()
        print(f"  - Menú {menu.menu} ({menu.id_modalidad.modalidad}): {preps} preparaciones")

        if preps > 0:
            # Verificar componentes en las preparaciones
            componentes_encontrados = set()
            for prep in TablaPreparaciones.objects.filter(id_menu=menu).prefetch_related('ingredientes__id_ingrediente_siesa__id_componente'):
                if prep.id_componente:
                    componentes_encontrados.add(prep.id_componente.componente)
                else:
                    for ing_rel in prep.ingredientes.all():
                        if ing_rel.id_ingrediente_siesa and ing_rel.id_ingrediente_siesa.id_componente:
                            componentes_encontrados.add(ing_rel.id_ingrediente_siesa.id_componente.componente)

            if componentes_encontrados:
                print(f"    Componentes detectados: {', '.join(sorted(componentes_encontrados))}")
else:
    print("❌ No existen los menús 1-5")
    print("   Solución: Crear menús con IA o manualmente")

# 5. Prueba de API Manual
print("\n5. PRUEBA DE VALIDACIÓN API")
print("-" * 60)

# Buscar el primer menú con modalidad
primer_menu = TablaMenus.objects.first()
if primer_menu:
    modalidad_id = primer_menu.id_modalidad.id_modalidades

    # Buscar primeros 5 menús de esa modalidad
    menus_prueba = TablaMenus.objects.filter(
        id_modalidad__id_modalidades=modalidad_id
    ).order_by('menu')[:5]

    if menus_prueba.count() >= 1:
        menu_ids = [str(m.id_menu) for m in menus_prueba]
        print(f"✓ Modalidad de prueba: {primer_menu.id_modalidad.modalidad}")
        print(f"✓ Menús a validar: {', '.join([m.menu for m in menus_prueba])}")
        print(f"✓ IDs: {', '.join(menu_ids)}")

        # Simular llamada a API
        print(f"\nURL de prueba:")
        print(f"/nutricion/api/validar-semana/?menu_ids={','.join(menu_ids)}&modalidad_id={modalidad_id}")

        # Verificar requerimientos para esa modalidad
        reqs_modalidad = RequerimientoSemanal.objects.filter(modalidad__id_modalidades=modalidad_id)
        if reqs_modalidad.exists():
            print(f"\n✓ Requerimientos configurados para esta modalidad: {reqs_modalidad.count()}")
            for req in reqs_modalidad[:3]:
                print(f"  - {req.componente.componente}: {req.frecuencia}x/semana")
        else:
            print(f"\n❌ NO hay requerimientos para modalidad {modalidad_id}")

print("\n" + "=" * 60)
print("FIN DEL DIAGNÓSTICO")
print("=" * 60)

# Resumen final
print("\n📊 RESUMEN:")
print(f"  - Requerimientos: {'✅' if total_reqs > 0 else '❌'}")
print(f"  - Ingredientes con componente: {'✅' if sin_componente == 0 else '❌'}")
print(f"  - Menús creados: {'✅' if total_menus > 0 else '❌'}")
print(f"  - Menús con preparaciones: {'✅' if menus_con_prep > 0 else '❌'}")

if total_reqs > 0 and sin_componente == 0 and menus_con_prep > 0:
    print("\n✅ SISTEMA FUNCIONANDO: Todos los componentes están configurados correctamente")
    print("   Si no ve los validadores en la interfaz:")
    print("   1. Hacer hard refresh del navegador (Ctrl+Shift+R)")
    print("   2. Revisar consola del navegador (F12) por errores")
    print("   3. Verificar que los menús tienen la modalidad correcta asignada")
else:
    print("\n⚠️  ATENCIÓN: Hay componentes faltantes")
    if total_reqs == 0:
        print("   - Ejecutar migración de requerimientos semanales")
    if sin_componente > 0:
        print("   - Asignar componentes a ingredientes faltantes")
    if menus_con_prep == 0:
        print("   - Crear preparaciones para los menús")

print()
