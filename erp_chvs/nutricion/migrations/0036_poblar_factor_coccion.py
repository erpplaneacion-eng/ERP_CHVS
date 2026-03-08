"""
Migración de datos: pobla factor_coccion en nutricion_tabla_alimentos_2018_icb
según los ingredientes reales usados en las preparaciones del sistema.

Reglas aplicadas (basadas en tabla PAE Colombia):
  Cereales absorbentes (arroz, pasta, maíz)  → 2.25 / 2.0
  Tubérculos y plátanos cocidos              → 1.10
  Leguminosas secas                          → 2.40
  Carnes de res / cerdo                      → 0.57
  Pollo                                      → 0.75
  Pescado                                    → 0.65
  Verduras cocidas                           → 0.90
  Todo lo demás (frutas, lácteos, condimentos,
    productos ya procesados, grasas, azúcares) → 1.00  (valor por defecto)
"""

from django.db import migrations


# Mapa código ICBF → factor de cocción
# Solo se listan los que difieren de 1.00 (default).
FACTORES = {
    # ── GRUPO I: Cereales absorbentes ─────────────────────────────────────
    "A010": "2.25",   # Arroz blanco, pulido, crudo
    "A074": "2.25",   # Pasta alimenticia, sin enriquecer, cruda
    "A072": "2.25",   # Pasta alimenticia, enriquecida, cruda
    "A045": "2.00",   # Maíz blanco, crudo

    # ── GRUPO I: Tubérculos y plátanos (cocidos) ───────────────────────────
    "B074": "1.10",   # Papa variedad harinosa, pastusa, con cáscara, cruda
    "B071": "1.10",   # Papa variedad harinosa, criolla, con cáscara, cruda
    "B089": "1.10",   # Plátano hartón, maduro, crudo
    "B092": "1.10",   # Plátano hartón, verde, crudo
    "B082": "1.10",   # Plátano áfrica, maduro, crudo
    "B107": "1.10",   # Yuca blanca, sin cáscara, cruda

    # ── GRUPO II: Verduras (cocidas / salteadas) ───────────────────────────
    "B027": "0.90",   # Cebolla cabezona, cruda
    "B103": "0.90",   # Tomate, crudo
    "B110": "0.90",   # Zanahoria, sin cáscara, cruda
    "B109": "0.90",   # Zanahoria, sin cáscara, cocida sin sal
    "B111": "0.90",   # Zapallo, crudo
    "B044": "0.90",   # Espinaca, cruda
    "B052": "0.90",   # Habichuela, cruda
    "B099": "0.90",   # Repollo blanco, crudo

    # ── GRUPO IV: Carnes de res y cerdo ───────────────────────────────────
    "F099": "0.57",   # Res, carne magra, cruda
    "138 UdeA": "0.57",   # Cerdo lomo o cañón ~12% grasa, crudo
    "138 TCA UdeA": "0.57",   # Cerdo lomo o cañón ~12% grasa, crudo (alias)

    # ── GRUPO IV: Pollo ───────────────────────────────────────────────────
    "F085": "0.75",           # Pollo, pechuga con piel, cruda
    "225 TCA UdeA": "0.75",   # AVES Pollo Pechuga, carne sin piel cruda

    # ── GRUPO IV: Pescado ─────────────────────────────────────────────────
    "El Dorado": "0.65",   # Lomitos de tilapia

    # ── GRUPO IV: Leguminosas secas ───────────────────────────────────────
    "T026": "2.40",   # Lenteja común, cruda
    "T015": "2.40",   # Frijol nima, crudo
    "T003": "2.40",   # Arveja seca, cruda
}


def poblar_factores(apps, schema_editor):
    TablaAlimentos = apps.get_model('nutricion', 'TablaAlimentos2018Icbf')
    for codigo, factor in FACTORES.items():
        TablaAlimentos.objects.filter(codigo=codigo).update(factor_coccion=factor)


def revertir_factores(apps, schema_editor):
    TablaAlimentos = apps.get_model('nutricion', 'TablaAlimentos2018Icbf')
    TablaAlimentos.objects.filter(codigo__in=FACTORES.keys()).update(factor_coccion='1.00')


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0035_tablaalimentos2018icbf_factor_coccion'),
    ]

    operations = [
        migrations.RunPython(poblar_factores, revertir_factores),
    ]
