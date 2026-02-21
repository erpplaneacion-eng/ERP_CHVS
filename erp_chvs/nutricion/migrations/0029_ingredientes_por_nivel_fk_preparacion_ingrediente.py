from django.db import migrations, models
import django.db.models.deletion


def poblar_fk_preparacion_ingrediente(apps, schema_editor):
    IngredientesPorNivel = apps.get_model('nutricion', 'TablaIngredientesPorNivel')
    PreparacionIngrediente = apps.get_model('nutricion', 'TablaPreparacionIngredientes')

    relaciones = {
        (id_preparacion, str(id_ingrediente)): rel_id
        for rel_id, id_preparacion, id_ingrediente in PreparacionIngrediente.objects.values_list(
            'id',
            'id_preparacion_id',
            'id_ingrediente_siesa_id',
        )
    }

    para_actualizar = []
    para_borrar = []

    for registro in IngredientesPorNivel.objects.all().iterator():
        codigo = str(registro.codigo_icbf) if registro.codigo_icbf is not None else None
        rel_id = relaciones.get((registro.id_preparacion_id, codigo))
        if rel_id is None:
            para_borrar.append(registro.pk)
            continue

        registro.id_preparacion_ingrediente_id = rel_id
        para_actualizar.append(registro)

    if para_actualizar:
        IngredientesPorNivel.objects.bulk_update(
            para_actualizar,
            ['id_preparacion_ingrediente'],
            batch_size=1000,
        )

    if para_borrar:
        IngredientesPorNivel.objects.filter(pk__in=para_borrar).delete()


def noop_reverse(apps, schema_editor):
    # No-op: no se restauran huérfanos eliminados durante la migración forward.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0028_firma_nutricional_contrato'),
    ]

    operations = [
        migrations.AddField(
            model_name='tablaingredientespornivel',
            name='id_preparacion_ingrediente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column='id_preparacion_ingrediente',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='configuraciones_por_nivel',
                to='nutricion.tablapreparacioningredientes',
                verbose_name='Relación Preparación-Ingrediente',
            ),
        ),
        migrations.RunPython(
            poblar_fk_preparacion_ingrediente,
            reverse_code=noop_reverse,
        ),
        migrations.AlterField(
            model_name='tablaingredientespornivel',
            name='id_preparacion_ingrediente',
            field=models.ForeignKey(
                db_column='id_preparacion_ingrediente',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='configuraciones_por_nivel',
                to='nutricion.tablapreparacioningredientes',
                verbose_name='Relación Preparación-Ingrediente',
            ),
        ),
    ]
