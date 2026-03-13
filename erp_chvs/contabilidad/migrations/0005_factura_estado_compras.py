from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0004_verificacion_por_factura'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='estado_compras',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('APROBADA', 'Aprobada por Compras'),
                    ('DEVUELTA', 'Devuelta al Líder'),
                ],
                default='PENDIENTE',
                max_length=10,
                verbose_name='Estado Compras',
            ),
        ),
        migrations.AddField(
            model_name='factura',
            name='comentario_devolucion',
            field=models.TextField(blank=True, verbose_name='Motivo de Devolución'),
        ),
    ]
