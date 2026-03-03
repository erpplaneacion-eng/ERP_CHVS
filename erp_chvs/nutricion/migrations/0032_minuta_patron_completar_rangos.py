"""
Migración de datos: completar MinutaPatronMeta (nutricion_minuta_patron_rangos).

Agrega las combinaciones (modalidad, componente, grupo) faltantes con sus rangos
por nivel escolar, según la configuración acordada de la Minuta Patrón ICBF.

Niveles escolares usados:
  '100'  → Prescolar
  '123'  → Primaria 1-2-3
  '45'   → Primaria 4-5
  '6789' → Secundaria
  '1011' → Media / Ciclo Complementario

Modalidades:
  '20501'  → COMPLEMENTO AM/PM PREPARADO
  '20507'  → COMPLEMENTO PM PREPARADO
  '20502'  → COMPLEMENTO AM/PM INDUSTRIALIZADO
  '20503'  → COMPLEMENTO AM/PM JORNADA ÚNICA
  '20510'  → REFUERZO COMPLEMENTO AM/PM PREPARADO
  '020511' → REFUERZO COMPLEMENTO AM/PM INDUSTRIALIZADO
"""

from django.db import migrations

NIVELES = ['100', '123', '45', '6789', '1011']


def _bulk_insert(MinutaPatronMeta, rows):
    """
    rows: lista de dicts con claves:
        modalidad, nivel, componente, grupo, minimo, maximo
    """
    objs = [
        MinutaPatronMeta(
            id_modalidad_id=r['modalidad'],
            id_grado_escolar_uapa_id=r['nivel'],
            id_componente_id=r['componente'],
            id_grupo_alimentos_id=r['grupo'],
            peso_neto_minimo=r['minimo'],
            peso_neto_maximo=r['maximo'],
        )
        for r in rows
    ]
    MinutaPatronMeta.objects.bulk_create(objs)


def agregar_rangos_faltantes(apps, schema_editor):
    MinutaPatronMeta = apps.get_model('nutricion', 'MinutaPatronMeta')

    # =========================================================
    # 20501 — COMPLEMENTO AM/PM PREPARADO
    # Nuevo: com2+g3 (copiar rangos de com2+g4), com1+g8 (sin rango), com16+g8 (sin rango)
    # =========================================================
    _20501_com2_g3 = [
        {'modalidad': '20501', 'nivel': '100',  'componente': 'com2', 'grupo': 'g3', 'minimo': 10, 'maximo': 63},
        {'modalidad': '20501', 'nivel': '123',  'componente': 'com2', 'grupo': 'g3', 'minimo': 20, 'maximo': 78},
        {'modalidad': '20501', 'nivel': '45',   'componente': 'com2', 'grupo': 'g3', 'minimo': 30, 'maximo': 110},
        {'modalidad': '20501', 'nivel': '6789', 'componente': 'com2', 'grupo': 'g3', 'minimo': 35, 'maximo': 140},
        {'modalidad': '20501', 'nivel': '1011', 'componente': 'com2', 'grupo': 'g3', 'minimo': 45, 'maximo': 172},
    ]
    _20501_com1_g8 = [
        {'modalidad': '20501', 'nivel': n, 'componente': 'com1', 'grupo': 'g8', 'minimo': None, 'maximo': None}
        for n in NIVELES
    ]
    _20501_especias = [
        {'modalidad': '20501', 'nivel': n, 'componente': 'com16', 'grupo': 'g8', 'minimo': None, 'maximo': None}
        for n in NIVELES
    ]
    _bulk_insert(MinutaPatronMeta, _20501_com2_g3 + _20501_com1_g8 + _20501_especias)

    # =========================================================
    # 20507 — COMPLEMENTO PM PREPARADO
    # Idéntico a 20501: mismos componentes nuevos, mismos rangos
    # =========================================================
    _20507_com2_g3 = [
        {'modalidad': '20507', 'nivel': '100',  'componente': 'com2', 'grupo': 'g3', 'minimo': 10, 'maximo': 63},
        {'modalidad': '20507', 'nivel': '123',  'componente': 'com2', 'grupo': 'g3', 'minimo': 20, 'maximo': 78},
        {'modalidad': '20507', 'nivel': '45',   'componente': 'com2', 'grupo': 'g3', 'minimo': 30, 'maximo': 110},
        {'modalidad': '20507', 'nivel': '6789', 'componente': 'com2', 'grupo': 'g3', 'minimo': 35, 'maximo': 140},
        {'modalidad': '20507', 'nivel': '1011', 'componente': 'com2', 'grupo': 'g3', 'minimo': 45, 'maximo': 172},
    ]
    _20507_com1_g8 = [
        {'modalidad': '20507', 'nivel': n, 'componente': 'com1', 'grupo': 'g8', 'minimo': None, 'maximo': None}
        for n in NIVELES
    ]
    _20507_especias = [
        {'modalidad': '20507', 'nivel': n, 'componente': 'com16', 'grupo': 'g8', 'minimo': None, 'maximo': None}
        for n in NIVELES
    ]
    _bulk_insert(MinutaPatronMeta, _20507_com2_g3 + _20507_com1_g8 + _20507_especias)

    # =========================================================
    # 20502 — COMPLEMENTO AM/PM INDUSTRIALIZADO
    # Nuevo: com13+g6 (copiar rangos de com13+g4 misma modalidad)
    # =========================================================
    _20502_com13_g6 = [
        {'modalidad': '20502', 'nivel': '100',  'componente': 'com13', 'grupo': 'g6', 'minimo': 12, 'maximo': 40},
        {'modalidad': '20502', 'nivel': '123',  'componente': 'com13', 'grupo': 'g6', 'minimo': 12, 'maximo': 40},
        {'modalidad': '20502', 'nivel': '45',   'componente': 'com13', 'grupo': 'g6', 'minimo': 13, 'maximo': 50},
        {'modalidad': '20502', 'nivel': '6789', 'componente': 'com13', 'grupo': 'g6', 'minimo': 13, 'maximo': 50},
        {'modalidad': '20502', 'nivel': '1011', 'componente': 'com13', 'grupo': 'g6', 'minimo': 13, 'maximo': 50},
    ]
    _bulk_insert(MinutaPatronMeta, _20502_com13_g6)

    # =========================================================
    # 20503 — COMPLEMENTO AM/PM JORNADA ÚNICA
    # Nuevo: com16+g8 (Especias, sin rango)
    # =========================================================
    _20503_especias = [
        {'modalidad': '20503', 'nivel': n, 'componente': 'com16', 'grupo': 'g8', 'minimo': None, 'maximo': None}
        for n in NIVELES
    ]
    _bulk_insert(MinutaPatronMeta, _20503_especias)

    # =========================================================
    # 20510 — REFUERZO COMPLEMENTO AM/PM PREPARADO
    # Todo nuevo, referencia: rangos de 20503 para cada componente
    # =========================================================

    # com2 + g4 (Alimento proteico — tomado de 20503, incluye dos sub-rangos por nivel)
    _20510_com2_g4 = [
        {'modalidad': '20510', 'nivel': '100',  'componente': 'com2', 'grupo': 'g4', 'minimo': 38, 'maximo': 50},
        {'modalidad': '20510', 'nivel': '100',  'componente': 'com2', 'grupo': 'g4', 'minimo': 5,  'maximo': 5},
        {'modalidad': '20510', 'nivel': '123',  'componente': 'com2', 'grupo': 'g4', 'minimo': 8,  'maximo': 8},
        {'modalidad': '20510', 'nivel': '123',  'componente': 'com2', 'grupo': 'g4', 'minimo': 44, 'maximo': 55},
        {'modalidad': '20510', 'nivel': '45',   'componente': 'com2', 'grupo': 'g4', 'minimo': 50, 'maximo': 63},
        {'modalidad': '20510', 'nivel': '45',   'componente': 'com2', 'grupo': 'g4', 'minimo': 17, 'maximo': 17},
        {'modalidad': '20510', 'nivel': '6789', 'componente': 'com2', 'grupo': 'g4', 'minimo': 50, 'maximo': 78},
        {'modalidad': '20510', 'nivel': '6789', 'componente': 'com2', 'grupo': 'g4', 'minimo': 25, 'maximo': 25},
        {'modalidad': '20510', 'nivel': '1011', 'componente': 'com2', 'grupo': 'g4', 'minimo': 50, 'maximo': 94},
        {'modalidad': '20510', 'nivel': '1011', 'componente': 'com2', 'grupo': 'g4', 'minimo': 40, 'maximo': 40},
    ]

    # com5 + g6 (Azúcares)
    _20510_com5_g6 = [
        {'modalidad': '20510', 'nivel': '100',  'componente': 'com5', 'grupo': 'g6', 'minimo': 6, 'maximo': 8},
        {'modalidad': '20510', 'nivel': '123',  'componente': 'com5', 'grupo': 'g6', 'minimo': 6, 'maximo': 8},
        {'modalidad': '20510', 'nivel': '45',   'componente': 'com5', 'grupo': 'g6', 'minimo': 6, 'maximo': 8},
        {'modalidad': '20510', 'nivel': '6789', 'componente': 'com5', 'grupo': 'g6', 'minimo': 8, 'maximo': 10},
        {'modalidad': '20510', 'nivel': '1011', 'componente': 'com5', 'grupo': 'g6', 'minimo': 8, 'maximo': 10},
    ]

    # com14 + g2 (Bebida)
    _20510_com14_g2 = [
        {'modalidad': '20510', 'nivel': n, 'componente': 'com14', 'grupo': 'g2', 'minimo': 60, 'maximo': 65}
        for n in NIVELES
    ]

    # com9 + g2 (Ensalada o verdura caliente) — maximo 0 = abierto
    _20510_com9_g2 = [
        {'modalidad': '20510', 'nivel': '100',  'componente': 'com9', 'grupo': 'g2', 'minimo': 50, 'maximo': 0},
        {'modalidad': '20510', 'nivel': '123',  'componente': 'com9', 'grupo': 'g2', 'minimo': 60, 'maximo': 0},
        {'modalidad': '20510', 'nivel': '45',   'componente': 'com9', 'grupo': 'g2', 'minimo': 65, 'maximo': 0},
        {'modalidad': '20510', 'nivel': '6789', 'componente': 'com9', 'grupo': 'g2', 'minimo': 70, 'maximo': 0},
        {'modalidad': '20510', 'nivel': '1011', 'componente': 'com9', 'grupo': 'g2', 'minimo': 90, 'maximo': 0},
    ]

    # com8 + g1 (Tubérculos, raíces, plátanos)
    _20510_com8_g1 = [
        {'modalidad': '20510', 'nivel': '100',  'componente': 'com8', 'grupo': 'g1', 'minimo': 40, 'maximo': 62},
        {'modalidad': '20510', 'nivel': '123',  'componente': 'com8', 'grupo': 'g1', 'minimo': 50, 'maximo': 70},
        {'modalidad': '20510', 'nivel': '45',   'componente': 'com8', 'grupo': 'g1', 'minimo': 50, 'maximo': 95},
        {'modalidad': '20510', 'nivel': '6789', 'componente': 'com8', 'grupo': 'g1', 'minimo': 65, 'maximo': 110},
        {'modalidad': '20510', 'nivel': '1011', 'componente': 'com8', 'grupo': 'g1', 'minimo': 80, 'maximo': 140},
    ]

    # com7 + g1 (Cereales)
    _20510_com7_g1 = [
        {'modalidad': '20510', 'nivel': '100',  'componente': 'com7', 'grupo': 'g1', 'minimo': 24, 'maximo': 26},
        {'modalidad': '20510', 'nivel': '123',  'componente': 'com7', 'grupo': 'g1', 'minimo': 31, 'maximo': 37},
        {'modalidad': '20510', 'nivel': '45',   'componente': 'com7', 'grupo': 'g1', 'minimo': 40, 'maximo': 46},
        {'modalidad': '20510', 'nivel': '6789', 'componente': 'com7', 'grupo': 'g1', 'minimo': 56, 'maximo': 60},
        {'modalidad': '20510', 'nivel': '1011', 'componente': 'com7', 'grupo': 'g1', 'minimo': 62, 'maximo': 64},
    ]

    # com16 + g8 (Especias, sin rango)
    _20510_especias = [
        {'modalidad': '20510', 'nivel': n, 'componente': 'com16', 'grupo': 'g8', 'minimo': None, 'maximo': None}
        for n in NIVELES
    ]

    _bulk_insert(
        MinutaPatronMeta,
        _20510_com2_g4 + _20510_com5_g6 + _20510_com14_g2 +
        _20510_com9_g2 + _20510_com8_g1 + _20510_com7_g1 + _20510_especias
    )

    # =========================================================
    # 020511 — REFUERZO COMPLEMENTO AM/PM INDUSTRIALIZADO
    # Nuevo: com2+g4, com2+g3, com14+g2, com14+g3
    # Rangos com2: referencia 20501/20507. Rangos com14: referencia 20503
    # =========================================================

    # com2 + g4
    _020511_com2_g4 = [
        {'modalidad': '020511', 'nivel': '100',  'componente': 'com2', 'grupo': 'g4', 'minimo': 10, 'maximo': 63},
        {'modalidad': '020511', 'nivel': '123',  'componente': 'com2', 'grupo': 'g4', 'minimo': 20, 'maximo': 78},
        {'modalidad': '020511', 'nivel': '45',   'componente': 'com2', 'grupo': 'g4', 'minimo': 30, 'maximo': 110},
        {'modalidad': '020511', 'nivel': '6789', 'componente': 'com2', 'grupo': 'g4', 'minimo': 35, 'maximo': 140},
        {'modalidad': '020511', 'nivel': '1011', 'componente': 'com2', 'grupo': 'g4', 'minimo': 45, 'maximo': 172},
    ]

    # com2 + g3 (mismos rangos que com2+g4)
    _020511_com2_g3 = [
        {'modalidad': '020511', 'nivel': '100',  'componente': 'com2', 'grupo': 'g3', 'minimo': 10, 'maximo': 63},
        {'modalidad': '020511', 'nivel': '123',  'componente': 'com2', 'grupo': 'g3', 'minimo': 20, 'maximo': 78},
        {'modalidad': '020511', 'nivel': '45',   'componente': 'com2', 'grupo': 'g3', 'minimo': 30, 'maximo': 110},
        {'modalidad': '020511', 'nivel': '6789', 'componente': 'com2', 'grupo': 'g3', 'minimo': 35, 'maximo': 140},
        {'modalidad': '020511', 'nivel': '1011', 'componente': 'com2', 'grupo': 'g3', 'minimo': 45, 'maximo': 172},
    ]

    # com14 + g2 (Bebida — referencia 20503: 60-65g todos los niveles)
    _020511_com14_g2 = [
        {'modalidad': '020511', 'nivel': n, 'componente': 'com14', 'grupo': 'g2', 'minimo': 60, 'maximo': 65}
        for n in NIVELES
    ]

    # com14 + g3 (mismos rangos que com14+g2)
    _020511_com14_g3 = [
        {'modalidad': '020511', 'nivel': n, 'componente': 'com14', 'grupo': 'g3', 'minimo': 60, 'maximo': 65}
        for n in NIVELES
    ]

    _bulk_insert(
        MinutaPatronMeta,
        _020511_com2_g4 + _020511_com2_g3 + _020511_com14_g2 + _020511_com14_g3
    )


def revertir_rangos_faltantes(apps, schema_editor):
    MinutaPatronMeta = apps.get_model('nutricion', 'MinutaPatronMeta')

    # Eliminar exactamente lo que se agregó en la migración forward
    eliminaciones = [
        # 20501
        {'id_modalidad_id': '20501', 'id_componente_id': 'com2',  'id_grupo_alimentos_id': 'g3'},
        {'id_modalidad_id': '20501', 'id_componente_id': 'com1',  'id_grupo_alimentos_id': 'g8'},
        {'id_modalidad_id': '20501', 'id_componente_id': 'com16', 'id_grupo_alimentos_id': 'g8'},
        # 20507
        {'id_modalidad_id': '20507', 'id_componente_id': 'com2',  'id_grupo_alimentos_id': 'g3'},
        {'id_modalidad_id': '20507', 'id_componente_id': 'com1',  'id_grupo_alimentos_id': 'g8'},
        {'id_modalidad_id': '20507', 'id_componente_id': 'com16', 'id_grupo_alimentos_id': 'g8'},
        # 20502
        {'id_modalidad_id': '20502', 'id_componente_id': 'com13', 'id_grupo_alimentos_id': 'g6'},
        # 20503
        {'id_modalidad_id': '20503', 'id_componente_id': 'com16', 'id_grupo_alimentos_id': 'g8'},
        # 20510
        {'id_modalidad_id': '20510', 'id_componente_id': 'com2',  'id_grupo_alimentos_id': 'g4'},
        {'id_modalidad_id': '20510', 'id_componente_id': 'com5',  'id_grupo_alimentos_id': 'g6'},
        {'id_modalidad_id': '20510', 'id_componente_id': 'com14', 'id_grupo_alimentos_id': 'g2'},
        {'id_modalidad_id': '20510', 'id_componente_id': 'com9',  'id_grupo_alimentos_id': 'g2'},
        {'id_modalidad_id': '20510', 'id_componente_id': 'com8',  'id_grupo_alimentos_id': 'g1'},
        {'id_modalidad_id': '20510', 'id_componente_id': 'com7',  'id_grupo_alimentos_id': 'g1'},
        {'id_modalidad_id': '20510', 'id_componente_id': 'com16', 'id_grupo_alimentos_id': 'g8'},
        # 020511
        {'id_modalidad_id': '020511', 'id_componente_id': 'com2',  'id_grupo_alimentos_id': 'g4'},
        {'id_modalidad_id': '020511', 'id_componente_id': 'com2',  'id_grupo_alimentos_id': 'g3'},
        {'id_modalidad_id': '020511', 'id_componente_id': 'com14', 'id_grupo_alimentos_id': 'g2'},
        {'id_modalidad_id': '020511', 'id_componente_id': 'com14', 'id_grupo_alimentos_id': 'g3'},
    ]
    for filtro in eliminaciones:
        MinutaPatronMeta.objects.filter(**filtro).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0031_alter_grupoexcluyenteset_id_and_more'),
    ]

    operations = [
        migrations.RunPython(
            agregar_rangos_faltantes,
            revertir_rangos_faltantes,
        ),
    ]
