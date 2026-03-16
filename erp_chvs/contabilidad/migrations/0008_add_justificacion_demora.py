from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0007_add_fecha_recepcion_lider_to_factura'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrocontable',
            name='justificacion_demora_lider',
            field=models.TextField(blank=True, verbose_name='Justificación Demora Líder'),
        ),
        migrations.AddField(
            model_name='registrocontable',
            name='justificacion_demora_compras',
            field=models.TextField(blank=True, verbose_name='Justificación Demora Compras'),
        ),
        migrations.AddField(
            model_name='registrocontable',
            name='justificacion_demora_contabilidad',
            field=models.TextField(blank=True, verbose_name='Justificación Demora Contabilidad'),
        ),
    ]
