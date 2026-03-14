from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0005_factura_estado_compras'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrocontable',
            name='registro_origen',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='registros_derivados',
                to='contabilidad.registrocontable',
                verbose_name='Registro Origen',
            ),
        ),
    ]
