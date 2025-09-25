# Generated manually to remove unique constraint

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0002_rename_facturacion_listado_ano_etc_idx_listados_fo_ano_e04e90_idx_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='listadosfocalizacion',
            name='unique_doc_ano_focalizacion',
        ),
    ]
