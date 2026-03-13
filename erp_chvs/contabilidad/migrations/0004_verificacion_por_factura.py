from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0003_items_checklist_iniciales'),
    ]

    operations = [
        # 1. Eliminar unique_together antigua
        migrations.AlterUniqueTogether(
            name='verificacionchecklist',
            unique_together=set(),
        ),
        # 2. Limpiar todas las filas existentes (datos de prueba, no hay prod aún)
        migrations.RunSQL(
            sql='DELETE FROM contabilidad_verificaciones;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3. Eliminar FK antigua a RegistroContable
        migrations.RemoveField(
            model_name='verificacionchecklist',
            name='registro',
        ),
        # 4. Agregar FK nueva a Factura (nullable temporalmente para evitar default)
        migrations.AddField(
            model_name='verificacionchecklist',
            name='factura',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='verificaciones',
                to='contabilidad.factura',
                verbose_name='Factura',
            ),
        ),
        # 5. Hacer el campo NOT NULL
        migrations.AlterField(
            model_name='verificacionchecklist',
            name='factura',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='verificaciones',
                to='contabilidad.factura',
                verbose_name='Factura',
            ),
        ),
        # 6. Establecer nueva unique_together
        migrations.AlterUniqueTogether(
            name='verificacionchecklist',
            unique_together={('factura', 'item')},
        ),
    ]
