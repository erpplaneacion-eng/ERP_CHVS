from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agente', '0002_generacion_ia_modalidad_menu_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='generacionia',
            name='ocasion_especial',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ocasión Especial'),
        ),
    ]
