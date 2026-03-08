from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0033_agregar_grupo_a_preparacion_ingredientes'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcedimientoPreparacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(
                    max_length=255,
                    verbose_name='Nombre de la preparación',
                    help_text='Nombre canónico. El generador Excel buscará coincidencias difusas con este campo.',
                )),
                ('procedimiento', models.TextField(
                    verbose_name='Procedimiento de preparación',
                    help_text='Paso a paso de elaboración.',
                )),
                ('activo', models.BooleanField(
                    default=True,
                    verbose_name='Activo',
                    help_text='Desactivar para excluir del matching sin borrar el registro.',
                )),
            ],
            options={
                'verbose_name': 'Procedimiento de Preparación',
                'verbose_name_plural': 'Procedimientos de Preparación',
                'db_table': 'nutricion_procedimiento_preparacion',
                'ordering': ['nombre'],
            },
        ),
    ]
