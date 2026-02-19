from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Convierte de IntegerField a DecimalField los 11 campos numéricos de
    TablaAlimentos2018Icbf que podían contener decimales pero los truncaban.

    Campos convertidos:
        energia_kcal, energia_kj, calcio_mg, sodio_mg, fosforo_mg,
        magnesio_mg, potasio_mg, vitamina_c_mg, vitamina_a_er,
        colesterol_mg, parte_comestible_porcentaje

    En PostgreSQL el cast INTEGER → NUMERIC es seguro y no requiere
    conversión de datos: los valores existentes se preservan íntegros.
    """

    dependencies = [
        ('nutricion', '0022_ingredientes_por_nivel_usar_codigo_icbf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='energia_kcal',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Energía (kcal)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='energia_kj',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Energía (kJ)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='calcio_mg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Calcio (mg)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='sodio_mg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Sodio (mg)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='fosforo_mg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Fósforo (mg)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='magnesio_mg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Magnesio (mg)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='potasio_mg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Potasio (mg)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='vitamina_c_mg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Vitamina C (mg)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='vitamina_a_er',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Vitamina A (ER)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='colesterol_mg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Colesterol (mg)'),
        ),
        migrations.AlterField(
            model_name='tablaalimentos2018icbf',
            name='parte_comestible_field',
            field=models.DecimalField(
                blank=True,
                db_column='parte_comestible_porcentaje',
                decimal_places=2,
                max_digits=5,
                null=True,
                verbose_name='Parte Comestible (%)',
            ),
        ),
    ]
