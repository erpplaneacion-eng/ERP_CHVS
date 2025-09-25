# Generated migration for ListadosFocalizacion model

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ListadosFocalizacion',
            fields=[
                ('id_listados', models.CharField(max_length=50, primary_key=True, serialize=False, unique=True, verbose_name='ID Listados')),
                ('ano', models.IntegerField(validators=[django.core.validators.MinValueValidator(2020)], verbose_name='Año')),
                ('etc', models.CharField(max_length=100, verbose_name='ETC (Entidad Territorial)')),
                ('institucion', models.CharField(max_length=200, verbose_name='Institución Educativa')),
                ('sede', models.CharField(max_length=200, verbose_name='Sede Educativa')),
                ('tipodoc', models.CharField(max_length=10, verbose_name='Tipo de Documento')),
                ('doc', models.CharField(max_length=20, verbose_name='Número de Documento')),
                ('apellido1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Primer Apellido')),
                ('apellido2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Segundo Apellido')),
                ('nombre1', models.CharField(max_length=100, verbose_name='Primer Nombre')),
                ('nombre2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Segundo Nombre')),
                ('fecha_nacimiento', models.CharField(max_length=20, verbose_name='Fecha de Nacimiento')),
                ('edad', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Edad')),
                ('etnia', models.CharField(blank=True, max_length=50, null=True, verbose_name='Etnia')),
                ('genero', models.CharField(max_length=10, verbose_name='Género')),
                ('grado_grupos', models.CharField(max_length=20, verbose_name='Grado y Grupos')),
                ('complemento_alimentario_preparado_am', models.CharField(blank=True, max_length=10, null=True, verbose_name='Complemento Alimentario AM')),
                ('complemento_alimentario_preparado_pm', models.CharField(blank=True, max_length=10, null=True, verbose_name='Complemento Alimentario PM')),
                ('almuerzo_jornada_unica', models.CharField(blank=True, max_length=10, null=True, verbose_name='Almuerzo Jornada Única')),
                ('refuerzo_complemento_am_pm', models.CharField(blank=True, max_length=10, null=True, verbose_name='Refuerzo Complemento AM/PM')),
                ('focalizacion', models.CharField(max_length=10, verbose_name='Focalización')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')),
            ],
            options={
                'verbose_name': 'Listado de Focalización',
                'verbose_name_plural': 'Listados de Focalización',
                'db_table': 'listados_focalizacion',
                'ordering': ['-ano', 'etc', 'institucion', 'sede'],
            },
        ),
        migrations.AddIndex(
            model_name='listadosfocalizacion',
            index=models.Index(fields=['ano', 'etc'], name='facturacion_listado_ano_etc_idx'),
        ),
        migrations.AddIndex(
            model_name='listadosfocalizacion',
            index=models.Index(fields=['focalizacion'], name='facturacion_listado_focalizacion_idx'),
        ),
        migrations.AddIndex(
            model_name='listadosfocalizacion',
            index=models.Index(fields=['sede'], name='facturacion_listado_sede_idx'),
        ),
        migrations.AddIndex(
            model_name='listadosfocalizacion',
            index=models.Index(fields=['doc'], name='facturacion_listado_doc_idx'),
        ),
        migrations.AddIndex(
            model_name='listadosfocalizacion',
            index=models.Index(fields=['fecha_creacion'], name='facturacion_listado_fecha_creacion_idx'),
        ),
        migrations.AddConstraint(
            model_name='listadosfocalizacion',
            constraint=models.UniqueConstraint(fields=('doc', 'ano', 'focalizacion'), name='unique_doc_ano_focalizacion'),
        ),
    ]