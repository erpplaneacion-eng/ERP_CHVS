# Migration split into 3 steps for safety:
# Step 1: Add nullable FK (this migration)
# Step 2: Populate existing rows (next migration)
# Step 3: Make non-nullable (next migration)

import django.db.models.deletion
from django.db import migrations, models


def poblar_tipo_programa_pae(apps, schema_editor):
    """Asignar tipo_programa='pae' a todos los programas existentes."""
    Programa = apps.get_model('planeacion', 'Programa')
    Programa.objects.filter(tipo_programa__isnull=True).update(tipo_programa_id='pae')


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('planeacion', '0004_add_item_to_sedes_educativas'),
        # Depende de 0010 que ya tiene los datos de TipoPrograma poblados
        ('principal', '0010_poblar_tipos_programa_y_nivel_general'),
    ]

    operations = [
        # Paso 1: Agregar FK nullable
        migrations.AddField(
            model_name='programa',
            name='tipo_programa',
            field=models.ForeignKey(
                db_column='tipo_programa',
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='principal.tipoprograma',
                verbose_name='Tipo de Programa',
            ),
        ),
        # Paso 2: Poblar con 'pae' en todos los registros existentes
        migrations.RunPython(poblar_tipo_programa_pae, revertir),
        # Paso 3: Hacer el campo non-nullable
        migrations.AlterField(
            model_name='programa',
            name='tipo_programa',
            field=models.ForeignKey(
                db_column='tipo_programa',
                null=False,
                on_delete=django.db.models.deletion.PROTECT,
                to='principal.tipoprograma',
                verbose_name='Tipo de Programa',
            ),
        ),
    ]
