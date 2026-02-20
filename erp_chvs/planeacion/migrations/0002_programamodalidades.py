import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planeacion', '0001_initial'),
        ('principal', '0004_delete_municipiomodalidades'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgramaModalidades',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('programa', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='modalidades_configuradas',
                    to='planeacion.programa',
                    verbose_name='Programa',
                )),
                ('modalidad', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='programas_asignados',
                    to='principal.modalidadesdeconsumo',
                    verbose_name='Modalidad',
                )),
            ],
            options={
                'verbose_name': 'Modalidad por Programa',
                'verbose_name_plural': 'Modalidades por Programa',
                'db_table': 'programa_modalidades',
                'ordering': ['programa__programa', 'modalidad__modalidad'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='programamodalidades',
            unique_together={('programa', 'modalidad')},
        ),
    ]
