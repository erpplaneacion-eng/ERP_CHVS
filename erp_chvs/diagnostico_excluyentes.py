"""
diagnostico_excluyentes.py
==========================
Diagnóstico completo del sistema de grupos excluyentes.

Ejecutar desde erp_chvs/:
    python manage.py shell < diagnostico_excluyentes.py

Responde:
  1. ¿Qué modalidades tienen GrupoExcluyenteSet configurado?
  2. ¿Esas modalidades tienen menús con preparaciones asignadas a los grupos del set?
  3. ¿El validador semanal debería mostrar tooltip para alguna semana?
"""

from nutricion.models import (
    GrupoExcluyenteSet,
    TablaMenus,
    TablaPreparaciones,
    RequerimientoSemanal,
)

SEP = "─" * 70

# ── 1. Sets configurados ─────────────────────────────────────────────────────
sets = (
    GrupoExcluyenteSet.objects
    .select_related('modalidad')
    .prefetch_related('miembros__grupo')
    .all()
)

print(SEP)
print("PASO 1 — Sets de grupos excluyentes en la base de datos")
print(SEP)

if not sets.exists():
    print("  ⚠️  No hay NINGÚN GrupoExcluyenteSet registrado.")
    print("  → Ve a /admin/nutricion/grupoexcluyenteset/ y crea el set.")
    print("     Ejemplo: modalidad 020511 · nombre 'G4-G6' · frecuencia 2")
    print("     Miembros: Grupo IV (carnes) + Grupo VI (azúcares)  ← ajusta a tu caso")
    print(SEP)
    raise SystemExit

for s in sets:
    grupos = [m.grupo for m in s.miembros.all()]
    nombres_grupos = " + ".join(f"{g.id_grupo_alimentos} ({g.grupo_alimentos[:40]})" for g in grupos)
    print(f"  SET id={s.id}  |  '{s.nombre}'")
    print(f"    Modalidad  : {s.modalidad.id_modalidades} – {s.modalidad.modalidad}")
    print(f"    Cuota/semana: {s.frecuencia_compartida}")
    print(f"    Grupos     : {nombres_grupos}")
    print()

# ── 2. Por cada set: ¿hay menús en esa modalidad? ───────────────────────────
print(SEP)
print("PASO 2 — Menús existentes por modalidad de cada set")
print(SEP)

for s in sets:
    modalidad = s.modalidad
    menus = TablaMenus.objects.filter(id_modalidad=modalidad).order_by('menu')
    print(f"  Modalidad {modalidad.id_modalidades}: {menus.count()} menús")

    if not menus.exists():
        print("    ⚠️  Sin menús → el validador no tiene datos que mostrar.")
        print()
        continue

    # Agrupar en semanas de 5
    menus_list = list(menus)
    for semana in range(1, 5):
        inicio = (semana - 1) * 5
        fin = inicio + 5
        menus_semana = menus_list[inicio:fin]
        if not menus_semana:
            break

        menu_ids = [m.id_menu for m in menus_semana]
        grupos_del_set = {m.grupo.id_grupo_alimentos for m in s.miembros.all()}

        # Contar preparaciones de los grupos del set en esta semana
        preps_set = (
            TablaPreparaciones.objects
            .filter(id_menu_id__in=menu_ids)
            .select_related('id_componente__id_grupo_alimentos')
        )

        conteo = {}
        for prep in preps_set:
            if prep.id_componente and prep.id_componente.id_grupo_alimentos:
                gid = prep.id_componente.id_grupo_alimentos.id_grupo_alimentos
                if gid in grupos_del_set:
                    conteo[gid] = conteo.get(gid, 0) + 1

        if conteo:
            detalle = "  ".join(f"{gid}={n}" for gid, n in conteo.items())
            print(f"    Semana {semana}: preparaciones en grupos del set → {detalle}  ✅ TOOLTIP debería aparecer")
        else:
            print(f"    Semana {semana}: ninguna preparación asignada a los grupos del set  ⚪ sin tooltip")

    print()

# ── 3. Requerimientos semanales configurados para la modalidad ───────────────
print(SEP)
print("PASO 3 — RequerimientoSemanal de las modalidades con sets")
print(SEP)

modalidades_con_set = {s.modalidad.id_modalidades for s in sets}
for mid in modalidades_con_set:
    reqs = RequerimientoSemanal.objects.filter(
        modalidad__id_modalidades=mid
    ).select_related('grupo')
    print(f"  Modalidad {mid}: {reqs.count()} requerimientos")
    for r in reqs:
        print(f"    {r.grupo.id_grupo_alimentos:6}  {r.grupo.grupo_alimentos[:50]:50}  freq={r.frecuencia}")
    print()

print(SEP)
print("DIAGNÓSTICO COMPLETO")
print(SEP)
