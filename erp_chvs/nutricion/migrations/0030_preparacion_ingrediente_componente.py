from django.db import migrations, models
import django.db.models.deletion


def backfill_componente_en_preparacion_ingrediente(apps, schema_editor):
    TablaPreparacionIngredientes = apps.get_model('nutricion', 'TablaPreparacionIngredientes')

    por_actualizar = []
    for rel in (
        TablaPreparacionIngredientes.objects
        .filter(id_componente__isnull=True)
        .select_related('id_preparacion')
        .iterator()
    ):
        comp_id = getattr(rel.id_preparacion, 'id_componente_id', None)
        if comp_id:
            rel.id_componente_id = comp_id
            por_actualizar.append(rel)

    if por_actualizar:
        TablaPreparacionIngredientes.objects.bulk_update(
            por_actualizar,
            ['id_componente'],
            batch_size=1000
        )


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0029_ingredientes_por_nivel_fk_preparacion_ingrediente'),
    ]

    operations = [
        migrations.AddField(
            model_name='tablapreparacioningredientes',
            name='id_componente',
            field=models.ForeignKey(
                blank=True,
                db_column='id_componente',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='ingredientes_preparacion',
                to='nutricion.componentesalimentos',
                verbose_name='Componente del Ingrediente en la Preparación',
            ),
        ),
        migrations.RunPython(
            backfill_componente_en_preparacion_ingrediente,
            reverse_code=noop_reverse,
        ),
    ]
