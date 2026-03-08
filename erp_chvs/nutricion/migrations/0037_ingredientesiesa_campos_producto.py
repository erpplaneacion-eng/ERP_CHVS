from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0036_poblar_factor_coccion'),
    ]

    operations = [
        migrations.AddField(
            model_name='tablaingredientessiesa',
            name='presentacion',
            field=models.CharField(
                blank=True, null=True, max_length=100,
                verbose_name='Presentación comercial',
                help_text='Ej: Bolsa 1000ml, Caja 500g, Bulto 50kg'
            ),
        ),
        migrations.AddField(
            model_name='tablaingredientessiesa',
            name='unidad_medida',
            field=models.CharField(
                blank=True, null=True, max_length=50,
                verbose_name='Unidad de medida',
                help_text='Ej: bolsa, caja, bulto, litro, unidad'
            ),
        ),
        migrations.AddField(
            model_name='tablaingredientessiesa',
            name='contenido_gramos',
            field=models.DecimalField(
                blank=True, null=True,
                max_digits=10, decimal_places=2,
                verbose_name='Contenido en gramos',
                help_text='Gramos por unidad. Ej: 1000 para Bolsa 1L'
            ),
        ),
        migrations.AlterModelOptions(
            name='tablaingredientessiesa',
            options={
                'ordering': ['nombre_ingrediente'],
                'verbose_name': 'Producto de Compras (Siesa)',
                'verbose_name_plural': 'Productos de Compras (Siesa)',
            },
        ),
    ]
