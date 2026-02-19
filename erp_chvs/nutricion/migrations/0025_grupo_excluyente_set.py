from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Crea las tablas para configurar grupos de alimentos excluyentes por modalidad.
    Un set excluyente agrupa varios grupos que comparten una cuota semanal combinada.
    """

    dependencies = [
        ('nutricion', '0024_requerimiento_semanal_usar_grupo'),
        ('principal', '0003_registroactividad'),
    ]

    operations = [
        migrations.CreateModel(
            name='GrupoExcluyenteSet',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(
                    max_length=100,
                    verbose_name='Nombre del Set',
                    help_text="Nombre descriptivo. Ej: 'G4-G6 proteína excluyente'"
                )),
                ('frecuencia_compartida', models.IntegerField(
                    verbose_name='Frecuencia Compartida',
                    help_text='Veces/semana que debe aparecer CUALQUIERA de los grupos del set en conjunto'
                )),
                ('modalidad', models.ForeignKey(
                    db_column='id_modalidades',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='grupos_excluyentes_sets',
                    to='principal.modalidadesdeconsumo',
                    verbose_name='Modalidad de Consumo'
                )),
            ],
            options={
                'verbose_name': 'Set de Grupos Excluyentes',
                'verbose_name_plural': 'Sets de Grupos Excluyentes',
                'db_table': 'nutricion_grupo_excluyente_set',
                'ordering': ['modalidad', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='GrupoExcluyenteSetMiembro',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('set_excluyente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='miembros',
                    to='nutricion.grupoexcluyenteset',
                    verbose_name='Set Excluyente'
                )),
                ('grupo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sets_excluyentes',
                    to='nutricion.gruposalimentos',
                    verbose_name='Grupo de Alimentos'
                )),
            ],
            options={
                'verbose_name': 'Miembro del Set Excluyente',
                'verbose_name_plural': 'Miembros del Set Excluyente',
                'db_table': 'nutricion_grupo_excluyente_set_miembro',
            },
        ),
        migrations.AlterUniqueTogether(
            name='grupoexcluyentesetmiembro',
            unique_together={('set_excluyente', 'grupo')},
        ),
    ]
