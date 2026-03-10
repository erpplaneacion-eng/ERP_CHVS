import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agente', '0001_initial'),
        ('principal', '0006_alter_registroactividad_modulo'),
    ]

    operations = [
        # Hacer id_menu nullable
        migrations.AlterField(
            model_name='generacionia',
            name='id_menu',
            field=models.ForeignKey(
                blank=True,
                db_column='id_menu',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='generaciones_ia',
                to='nutricion.tablamenus',
                verbose_name='Menú (destino)',
            ),
        ),
        # Agregar id_modalidad
        migrations.AddField(
            model_name='generacionia',
            name='id_modalidad',
            field=models.ForeignKey(
                db_column='id_modalidad',
                null=True,  # temporal para que no falle en filas existentes
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='generaciones_ia',
                to='principal.modalidadesdeconsumo',
                verbose_name='Modalidad',
            ),
        ),
    ]
