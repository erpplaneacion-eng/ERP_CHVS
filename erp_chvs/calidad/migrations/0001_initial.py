import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificadoCalidad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_certificado', models.CharField(editable=False, max_length=20, unique=True)),
                ('cedula', models.CharField(max_length=20, verbose_name='Cédula')),
                ('nombre_completo', models.CharField(max_length=200, verbose_name='Nombre Completo')),
                ('cargo', models.CharField(blank=True, max_length=200, verbose_name='Cargo')),
                ('programa_empresa', models.CharField(blank=True, max_length=300, verbose_name='Programa / Empresa')),
                ('eps', models.CharField(blank=True, max_length=200, verbose_name='EPS')),
                ('tipo_empleado', models.CharField(
                    choices=[
                        ('manipuladora', 'Manipuladora de Alimentos'),
                        ('planta', 'Personal de Planta'),
                        ('aprendiz', 'Aprendiz SENA'),
                    ],
                    max_length=20,
                    verbose_name='Tipo de Empleado',
                )),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('fecha_emision', models.DateField(auto_now_add=True, verbose_name='Fecha de Emisión')),
                ('creado_por', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Creado por',
                )),
            ],
            options={
                'verbose_name': 'Certificado de Calidad',
                'verbose_name_plural': 'Certificados de Calidad',
                'db_table': 'calidad_certificados',
                'ordering': ['-fecha_emision', '-id'],
            },
        ),
    ]
