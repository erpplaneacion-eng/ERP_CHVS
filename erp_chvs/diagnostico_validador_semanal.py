"""
diagnostico_validador_semanal.py
Ejecutar con: python manage.py shell < diagnostico_validador_semanal.py

Diagnostica el estado de los datos necesarios para el validador semanal
de las tarjetas de menú en lista_menus.html.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from django.db.models import Count

from nutricion.models import (
    RequerimientoSemanal,
    ComponentesAlimentos,
    ComponentesModalidades,
    TablaPreparaciones,
    TablaMenus,
)
from principal.models import ModalidadesDeConsumo

SEP = "=" * 60
SEP2 = "-" * 40

# ─────────────────────────────────────────────
# 1. REQUERIMIENTO SEMANAL
# ─────────────────────────────────────────────
print(SEP)
print("1. TABLA: nutricion_requerimientos_semanales (RequerimientoSemanal)")
print(SEP)
total = RequerimientoSemanal.objects.count()
print(f"   Total de registros: {total}")
if total > 0:
    for r in RequerimientoSemanal.objects.select_related('modalidad', 'componente').all():
        print(f"   Modalidad: {r.modalidad.modalidad!r:30s} | Componente: {r.componente.componente!r:35s} | Frecuencia: {r.frecuencia}x/semana")
else:
    print("   ⚠️  TABLA VACÍA — El validador siempre devuelve 'cumple: True, componentes: []'")

# ─────────────────────────────────────────────
# 2. MODALIDADES DE CONSUMO
# ─────────────────────────────────────────────
print()
print(SEP)
print("2. TABLA: ModalidadesDeConsumo (principal)")
print(SEP)
modalidades = ModalidadesDeConsumo.objects.all()
print(f"   Total de modalidades: {modalidades.count()}")
for m in modalidades:
    req_count = RequerimientoSemanal.objects.filter(modalidad=m).count()
    comp_count = ComponentesModalidades.objects.filter(id_modalidad=m).count()
    tiene_req = "✅" if req_count > 0 else "❌ SIN REQS"
    print(f"   ID={m.id_modalidades:>4} | {m.modalidad!r:45s} | ReqSemanal: {req_count:>2} {tiene_req} | CompModalidad: {comp_count:>2}")

# ─────────────────────────────────────────────
# 3. COMPONENTES DE ALIMENTOS
# ─────────────────────────────────────────────
print()
print(SEP)
print("3. TABLA: ComponentesAlimentos (nutricion)")
print(SEP)
componentes = ComponentesAlimentos.objects.all()
print(f"   Total de componentes: {componentes.count()}")
for c in componentes:
    reqs = RequerimientoSemanal.objects.filter(componente=c).count()
    mods = ComponentesModalidades.objects.filter(id_componente=c).count()
    print(f"   ID={c.id_componente:>4} | {c.componente!r:40s} | En ReqSemanal: {reqs:>2} | En CompModal: {mods:>2}")

# ─────────────────────────────────────────────
# 4. COMPONENTES POR MODALIDAD (tabla puente)
# ─────────────────────────────────────────────
print()
print(SEP)
print("4. TABLA: ComponentesModalidades (tabla puente)")
print(SEP)
total_cm = ComponentesModalidades.objects.count()
print(f"   Total de registros: {total_cm}")
if total_cm > 0:
    for cm in ComponentesModalidades.objects.select_related('id_modalidad', 'id_componente').all():
        print(f"   Modalidad: {cm.id_modalidad.modalidad!r:35s} | Componente: {cm.id_componente.componente!r}")
else:
    print("   ⚠️  TABLA VACÍA")

# ─────────────────────────────────────────────
# 5. PREPARACIONES: ¿TIENEN id_componente ASIGNADO?
# ─────────────────────────────────────────────
print()
print(SEP)
print("5. PREPARACIONES — estado de id_componente (lookup del validador)")
print(SEP)
total_prep = TablaPreparaciones.objects.count()
con_comp = TablaPreparaciones.objects.filter(id_componente__isnull=False).count()
sin_comp = TablaPreparaciones.objects.filter(id_componente__isnull=True).count()
print(f"   Total preparaciones: {total_prep}")
print(f"   Con id_componente asignado: {con_comp}  ({'✅' if con_comp > 0 else '⚠️ el validador buscará en ingredientes'})")
print(f"   Sin id_componente:          {sin_comp}")

if con_comp > 0:
    print(SEP2)
    print("   Ejemplos con componente asignado:")
    for p in TablaPreparaciones.objects.filter(id_componente__isnull=False).select_related('id_componente')[:10]:
        print(f"   Prep: {p.preparacion!r:35s} → Componente: {p.id_componente.componente!r}")

# ─────────────────────────────────────────────
# 6. SIMULACIÓN: ¿Qué devuelve api_validar_semana para el primer menú?
# ─────────────────────────────────────────────
print()
print(SEP)
print("6. SIMULACIÓN de api_validar_semana con los primeros menús encontrados")
print(SEP)

primer_menu = TablaMenus.objects.select_related('id_modalidad').first()
if primer_menu and primer_menu.id_modalidad:
    modalidad = primer_menu.id_modalidad
    # Tomar hasta 5 menús de esta modalidad
    menus_modalidad = list(
        TablaMenus.objects.filter(id_modalidad=modalidad).order_by('menu')[:5]
    )
    menu_ids = [m.id_menu for m in menus_modalidad]
    print(f"   Modalidad: {modalidad.modalidad!r}  (ID={modalidad.id_modalidades})")
    print(f"   Menús tomados: {menu_ids}")

    reqs = RequerimientoSemanal.objects.filter(modalidad=modalidad)
    print(f"   Requerimientos semanales para esta modalidad: {reqs.count()}")

    if reqs.count() == 0:
        print("   ⚠️  Sin requerimientos → la respuesta siempre será cumple=True, componentes=[]")
    else:
        from nutricion.models import TablaPreparacionIngredientes

        menus_por_componente = {}
        for menu_id in menu_ids:
            preparaciones = TablaPreparaciones.objects.filter(
                id_menu_id=menu_id
            ).prefetch_related('ingredientes__id_ingrediente_siesa__id_componente')

            componentes_del_menu = set()
            for prep in preparaciones:
                if prep.id_componente:
                    componentes_del_menu.add(prep.id_componente.id_componente)
                else:
                    for ing_rel in prep.ingredientes.all():
                        alimento = ing_rel.id_ingrediente_siesa
                        if alimento and alimento.id_componente:
                            componentes_del_menu.add(alimento.id_componente.id_componente)

            for comp_id in componentes_del_menu:
                if comp_id not in menus_por_componente:
                    menus_por_componente[comp_id] = set()
                menus_por_componente[comp_id].add(menu_id)

        print()
        print("   Resultado de validación:")
        cumple_total = True
        for req in reqs.select_related('componente'):
            comp_id = req.componente.id_componente
            actual = len(menus_por_componente.get(comp_id, set()))
            cumple = actual >= req.frecuencia
            if not cumple:
                cumple_total = False
            icono = "✅" if cumple else "❌"
            print(f"   {icono} {req.componente.componente!r:40s} | actual={actual} | requerido={req.frecuencia}")
        print(f"\n   cumple_total: {cumple_total}")
else:
    print("   ⚠️  No hay menús en la base de datos.")


# ─────────────────────────────────────────────
# 7. ANOMALÍAS: duplicados en RequerimientoSemanal
# ─────────────────────────────────────────────
print()
print(SEP)
print("7. ANOMALÍAS — duplicados en RequerimientoSemanal")
print(SEP)
duplicados = (
    RequerimientoSemanal.objects
    .values('modalidad', 'componente')
    .annotate(total=Count('id'))
    .filter(total__gt=1)
)
if duplicados.exists():
    print("   ⚠️  Se encontraron combinaciones duplicadas (viola unique_together):")
    for d in duplicados:
        modal = ModalidadesDeConsumo.objects.get(pk=d['modalidad'])
        comp  = ComponentesAlimentos.objects.get(pk=d['componente'])
        rows  = RequerimientoSemanal.objects.filter(
            modalidad=modal, componente=comp
        )
        print(f"   Modalidad: {modal.modalidad!r} | Componente: {comp.componente!r} | Frecuencias: {[r.frecuencia for r in rows]}")
else:
    print("   ✅ Sin duplicados detectados")

# ─────────────────────────────────────────────
# 8. MENÚS: ¿qué modalidades tienen menús pero NO tienen RequerimientoSemanal?
# ─────────────────────────────────────────────
print()
print(SEP)
print("8. MODALIDADES con menús pero SIN RequerimientoSemanal (el validador siempre OK)")
print(SEP)
modalidades_con_menus = (
    TablaMenus.objects.values('id_modalidad')
    .annotate(total=Count('id_menu'))
    .filter(total__gt=0)
)
encontrado_gap = False
for entry in modalidades_con_menus:
    modal_id = entry['id_modalidad']
    if modal_id is None:
        continue
    try:
        modal = ModalidadesDeConsumo.objects.get(pk=modal_id)
    except ModalidadesDeConsumo.DoesNotExist:
        continue
    req_count = RequerimientoSemanal.objects.filter(modalidad=modal).count()
    if req_count == 0:
        print(f"   ❌ {modal.modalidad!r} — {entry['total']} menús pero 0 requerimientos semanales")
        encontrado_gap = True
if not encontrado_gap:
    print("   ✅ Todas las modalidades con menús tienen requerimientos semanales definidos")

print()
print(SEP)
print("FIN DEL DIAGNÓSTICO")
print(SEP)
