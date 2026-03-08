from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0034_procedimiento_preparacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='tablaalimentos2018icbf',
            name='factor_coccion',
            field=models.DecimalField(
                decimal_places=2,
                default=1.0,
                help_text='Relación peso cocido / peso neto crudo. Por defecto 1.00 (sin cambio). Ej: arroz=2.25, pollo=0.75, leguminosas=2.4',
                max_digits=5,
                verbose_name='Factor de Cocción',
            ),
        ),
    ]
