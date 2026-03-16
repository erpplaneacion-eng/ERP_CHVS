from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0007_agregar_modulo_agente'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registroactividad',
            name='modulo',
            field=models.CharField(
                choices=[
                    ('facturacion', 'Facturación'),
                    ('nutricion', 'Nutrición'),
                    ('planeacion', 'Planeación'),
                    ('costos', 'Costos'),
                    ('logistica', 'Logística'),
                    ('principal', 'Datos Maestros'),
                    ('agente', 'Agente IA'),
                    ('dashboard', 'Dashboard'),
                    ('contabilidad', 'Contabilidad'),
                ],
                max_length=50,
                verbose_name='Módulo',
            ),
        ),
    ]
