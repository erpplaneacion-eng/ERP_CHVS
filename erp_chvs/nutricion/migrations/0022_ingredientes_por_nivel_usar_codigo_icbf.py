from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Refactoriza TablaIngredientesPorNivel para usar codigo_icbf como referencia al
    alimento ICBF en lugar de depender de TablaIngredientesSiesa (tabla vacía hasta
    que se implemente la integración con Siesa).

    Cambios:
    - id_ingrediente_siesa: NOT NULL → nullable (SET_NULL), para uso futuro con Siesa
    - unique_together: ('id_analisis', 'id_preparacion', 'id_ingrediente_siesa')
                    → ('id_analisis', 'id_preparacion', 'codigo_icbf')
    - ordering: ['id_preparacion', 'id_ingrediente_siesa']
              → ['id_preparacion', 'codigo_icbf']
    """

    dependencies = [
        ('nutricion', '0021_rename_nutricion_c_id_moda_c83791_idx_nutricion_c_id_moda_8d8f38_idx'),
    ]

    operations = [
        # 1. Eliminar la restricción unique_together anterior
        migrations.AlterUniqueTogether(
            name='tablaingredientespornivel',
            unique_together=set(),
        ),
        # 2. Hacer nullable la FK a TablaIngredientesSiesa
        migrations.AlterField(
            model_name='tablaingredientespornivel',
            name='id_ingrediente_siesa',
            field=models.ForeignKey(
                blank=True,
                db_column='id_ingrediente_siesa',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='configuraciones_por_nivel',
                to='nutricion.tablaingredientessiesa',
                verbose_name='Ingrediente Siesa',
            ),
        ),
        # 3. Establecer la nueva restricción unique_together con codigo_icbf
        migrations.AlterUniqueTogether(
            name='tablaingredientespornivel',
            unique_together={('id_analisis', 'id_preparacion', 'codigo_icbf')},
        ),
        # 4. Actualizar ordering en los metadatos del modelo
        migrations.AlterModelOptions(
            name='tablaingredientespornivel',
            options={
                'ordering': ['id_preparacion', 'codigo_icbf'],
                'verbose_name': 'Ingrediente Configurado por Nivel',
                'verbose_name_plural': 'Ingredientes Configurados por Nivel',
            },
        ),
    ]
