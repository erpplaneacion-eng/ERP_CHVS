from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0037_ingredientesiesa_campos_producto'),
        ('planeacion', '0004_add_item_to_sedes_educativas'),
    ]

    operations = [
        migrations.CreateModel(
            name='EquivalenciaICBFCompras',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('usuario', models.CharField(blank=True, max_length=100, null=True, verbose_name='Usuario que realizó el match')),
                ('id_alimento_icbf', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='equivalencias_compras',
                    to='nutricion.tablaalimentos2018icbf',
                    verbose_name='Alimento ICBF'
                )),
                ('id_programa', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='equivalencias_icbf',
                    to='planeacion.programa',
                    verbose_name='Programa/Contrato'
                )),
                ('id_ingrediente_compras', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='equivalencias_icbf',
                    to='nutricion.tablaingredientessiesa',
                    verbose_name='Producto de Compras'
                )),
            ],
            options={
                'verbose_name': 'Equivalencia ICBF → Compras',
                'verbose_name_plural': 'Equivalencias ICBF → Compras',
                'db_table': 'nutricion_equivalencia_icbf_compras',
                'unique_together': {('id_alimento_icbf', 'id_programa')},
            },
        ),
    ]
