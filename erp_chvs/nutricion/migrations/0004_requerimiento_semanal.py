# Generated manually 2026-02-12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0001_initial'),
        ('nutricion', '0003_renombrar_tabla_componentes_alimentos'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequerimientoSemanal',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('frecuencia', models.IntegerField(help_text='Número de veces que debe aparecer este componente en la semana', verbose_name='Frecuencia Semanal')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')),
                ('componente', models.ForeignKey(db_column='componente', on_delete=django.db.models.deletion.PROTECT, related_name='requerimientos_semanales', to='nutricion.componentesalimentos', verbose_name='Componente de Alimento')),
                ('modalidad', models.ForeignKey(db_column='modalidad', on_delete=django.db.models.deletion.PROTECT, related_name='requerimientos_semanales', to='principal.modalidadesdeconsumo', verbose_name='Modalidad de Consumo')),
            ],
            options={
                'verbose_name': 'Requerimiento Semanal',
                'verbose_name_plural': 'Requerimientos Semanales',
                'db_table': 'nutricion_requerimientos_semanales',
                'ordering': ['modalidad', 'componente'],
                'unique_together': {('modalidad', 'componente')},
                'indexes': [
                    models.Index(fields=['modalidad'], name='nutricion_r_modalid_idx'),
                    models.Index(fields=['componente'], name='nutricion_r_compone_idx'),
                ],
            },
        ),
    ]
