from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0009_add_observacion_retraso_to_factura'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='estado_contabilidad',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('APROBADA', 'Aprobada por Contabilidad'),
                    ('DEVUELTA', 'Devuelta a Compras'),
                ],
                default='PENDIENTE',
                max_length=10,
                verbose_name='Estado Contabilidad',
            ),
        ),
        migrations.AddField(
            model_name='factura',
            name='comentario_devolucion_contabilidad',
            field=models.TextField(
                blank=True,
                verbose_name='Motivo de Devolución Contabilidad',
            ),
        ),
    ]
