from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('planeacion', '0001_initial'),
        ('nutricion', '0027_recomendacion_diaria_grado_mod'),
    ]

    operations = [
        migrations.CreateModel(
            name='FirmaNutricionalContrato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('elabora_nombre', models.CharField(max_length=255, verbose_name='Nombre Dietista (Elabora)')),
                ('elabora_matricula', models.CharField(max_length=50, verbose_name='Matrícula Profesional (Elabora)')),
                ('elabora_firma_texto', models.CharField(blank=True, max_length=255, null=True, verbose_name='Firma Texto (Elabora)')),
                ('elabora_firma_imagen', models.ImageField(blank=True, null=True, upload_to='firmas_nutricion/', verbose_name='Firma Imagen (Elabora)')),
                ('aprueba_nombre', models.CharField(max_length=255, verbose_name='Nombre Dietista (Aprueba)')),
                ('aprueba_matricula', models.CharField(max_length=50, verbose_name='Matrícula Profesional (Aprueba)')),
                ('aprueba_firma_texto', models.CharField(blank=True, max_length=255, null=True, verbose_name='Firma Texto (Aprueba)')),
                ('aprueba_firma_imagen', models.ImageField(blank=True, null=True, upload_to='firmas_nutricion/', verbose_name='Firma Imagen (Aprueba)')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Fecha Actualización')),
                ('usuario_modificacion', models.CharField(blank=True, max_length=100, null=True, verbose_name='Usuario que Modificó')),
                ('programa', models.OneToOneField(db_column='id_contrato', on_delete=django.db.models.deletion.CASCADE, related_name='firma_nutricional', to='planeacion.programa', verbose_name='Contrato/Programa')),
            ],
            options={
                'verbose_name': 'Firma Nutricional por Contrato',
                'verbose_name_plural': 'Firmas Nutricionales por Contrato',
                'db_table': 'nutricion_firma_nutricional_contrato',
                'ordering': ['programa__programa'],
            },
        ),
    ]

