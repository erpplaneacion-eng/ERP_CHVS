from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0006_registro_origen'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='fecha_recepcion_lider',
            field=models.DateField(
                null=True,
                blank=True,
                verbose_name='Fecha de Recepción por Líder',
                help_text='Fecha en que el líder recibió físicamente este documento.',
            ),
        ),
    ]
