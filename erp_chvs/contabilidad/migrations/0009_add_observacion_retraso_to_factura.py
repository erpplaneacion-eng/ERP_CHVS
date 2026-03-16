from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0008_add_justificacion_demora'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='observacion_retraso',
            field=models.TextField(
                blank=True,
                verbose_name='Observación de Retraso',
                help_text='Explicación opcional del líder sobre el retraso entre la fecha de la factura y su carga al sistema.',
            ),
        ),
    ]
