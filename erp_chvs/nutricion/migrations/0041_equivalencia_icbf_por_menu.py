"""
Migración: EquivalenciaICBFCompras cambia de granularidad programa→menú.

Cambios:
  - Elimina es_principal (ya no aplica: 1 producto exacto por menú)
  - Agrega id_menu FK a TablaMenus
  - unique_together: (icbf, programa, siesa) → (icbf, programa, menu)

NOTA: borra todos los registros existentes antes de agregar la FK no-nullable.
Los datos previos eran del simulacro de desarrollo (no hay producción activa).
"""
import django.db.models.deletion
from django.db import migrations, models


def _borrar_equivalencias(apps, schema_editor):
    """Limpia datos del simulacro anterior (granularidad por programa)."""
    EquivalenciaICBFCompras = apps.get_model('nutricion', 'EquivalenciaICBFCompras')
    EquivalenciaICBFCompras.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0040_equivalencia_icbf_compras_1_a_n'),
    ]

    operations = [
        # 1. Limpiar datos de la iteración anterior
        migrations.RunPython(_borrar_equivalencias, migrations.RunPython.noop),

        # 2. Quitar unique_together viejo
        migrations.AlterUniqueTogether(
            name='equivalenciaicbfcompras',
            unique_together=set(),
        ),

        # 3. Eliminar campo es_principal
        migrations.RemoveField(
            model_name='equivalenciaicbfcompras',
            name='es_principal',
        ),

        # 4. Agregar FK id_menu (seguro porque ya no hay filas)
        migrations.AddField(
            model_name='equivalenciaicbfcompras',
            name='id_menu',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='equivalencias_compras',
                to='nutricion.tablamenus',
                verbose_name='Menú',
            ),
        ),

        # 5. Nuevo unique_together
        migrations.AlterUniqueTogether(
            name='equivalenciaicbfcompras',
            unique_together={('id_alimento_icbf', 'id_programa', 'id_menu')},
        ),
    ]
