from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0002_perfilusuario'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroActividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modulo', models.CharField(
                    choices=[
                        ('facturacion', 'Facturación'),
                        ('nutricion', 'Nutrición'),
                        ('planeacion', 'Planeación'),
                        ('principal', 'Datos Maestros'),
                        ('dashboard', 'Dashboard'),
                    ],
                    max_length=50,
                    verbose_name='Módulo',
                )),
                ('accion', models.CharField(max_length=100, verbose_name='Acción')),
                ('descripcion', models.TextField(blank=True, verbose_name='Detalle')),
                ('ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')),
                ('fecha', models.DateTimeField(auto_now_add=True, verbose_name='Fecha y hora')),
                ('exitoso', models.BooleanField(default=True, verbose_name='Exitoso')),
                ('usuario', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                )),
            ],
            options={
                'verbose_name': 'Registro de Actividad',
                'verbose_name_plural': 'Registros de Actividad',
                'db_table': 'principal_registro_actividad',
                'ordering': ['-fecha'],
            },
        ),
    ]
