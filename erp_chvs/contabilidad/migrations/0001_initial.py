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
            name='ItemChecklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre del Ítem')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('tipo_proceso', models.CharField(
                    choices=[('SERVICIOS', 'Servicios'), ('MATERIAS_PRIMAS', 'Materias Primas'), ('AMBOS', 'Ambos')],
                    default='AMBOS',
                    max_length=20,
                    verbose_name='Tipo de Proceso',
                )),
                ('obligatorio', models.BooleanField(default=True, verbose_name='Obligatorio')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('orden', models.PositiveSmallIntegerField(default=0, verbose_name='Orden')),
            ],
            options={
                'verbose_name': 'Ítem de Checklist',
                'verbose_name_plural': 'Ítems de Checklist',
                'db_table': 'contabilidad_items_checklist',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='RegistroContable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[('SERVICIOS', 'Servicios'), ('MATERIAS_PRIMAS', 'Materias Primas')],
                    max_length=20,
                    verbose_name='Tipo',
                )),
                ('periodo_mes', models.PositiveSmallIntegerField(verbose_name='Mes del Período')),
                ('periodo_ano', models.PositiveSmallIntegerField(verbose_name='Año del Período')),
                ('estado', models.CharField(
                    choices=[
                        ('BORRADOR', 'Borrador'),
                        ('ENVIADO', 'Enviado'),
                        ('EN_REVISION_COMPRAS', 'En Revisión Compras'),
                        ('DEVUELTO_COMPRAS', 'Devuelto por Compras'),
                        ('APROBADO_COMPRAS', 'Aprobado por Compras'),
                        ('OBSERVADO_CONTABILIDAD', 'Observado por Contabilidad'),
                        ('APROBADO_CONTABILIDAD', 'Aprobado por Contabilidad'),
                        ('CERRADO', 'Cerrado'),
                    ],
                    default='BORRADOR',
                    max_length=30,
                    verbose_name='Estado',
                )),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('fecha_envio', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Envío')),
                ('fecha_entrega_fisica', models.DateTimeField(blank=True, null=True, verbose_name='Fecha Entrega Física')),
                ('fecha_inicio_revision_compras', models.DateTimeField(blank=True, null=True, verbose_name='Inicio Revisión Compras')),
                ('fecha_devolucion_compras', models.DateTimeField(blank=True, null=True, verbose_name='Fecha Devolución Compras')),
                ('fecha_reenvio', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Reenvío')),
                ('fecha_reentrega_fisica', models.DateTimeField(blank=True, null=True, verbose_name='Fecha Reentrega Física')),
                ('fecha_aprobacion_compras', models.DateTimeField(blank=True, null=True, verbose_name='Fecha Aprobación Compras')),
                ('fecha_inicio_revision_contabilidad', models.DateTimeField(blank=True, null=True, verbose_name='Inicio Revisión Contabilidad')),
                ('fecha_observacion_contabilidad', models.DateTimeField(blank=True, null=True, verbose_name='Fecha Observación Contabilidad')),
                ('fecha_respuesta_compras', models.DateTimeField(blank=True, null=True, verbose_name='Fecha Respuesta Compras')),
                ('fecha_aprobacion_contabilidad', models.DateTimeField(blank=True, null=True, verbose_name='Fecha Aprobación Contabilidad')),
                ('fecha_cierre', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Cierre')),
                ('lider', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='registros_contables',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Líder',
                )),
            ],
            options={
                'verbose_name': 'Registro Contable',
                'verbose_name_plural': 'Registros Contables',
                'db_table': 'contabilidad_registros',
                'ordering': ['-fecha_creacion'],
                'indexes': [
                    models.Index(fields=['lider', 'periodo_ano', 'periodo_mes'], name='contabilida_lider_i_idx'),
                    models.Index(fields=['estado'], name='contabilida_estado_idx'),
                    models.Index(fields=['tipo', 'periodo_ano', 'periodo_mes'], name='contabilida_tipo_p_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='Factura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_factura', models.CharField(max_length=100, verbose_name='Número de Factura')),
                ('proveedor', models.CharField(max_length=200, verbose_name='Proveedor')),
                ('concepto', models.CharField(max_length=300, verbose_name='Concepto')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='Valor')),
                ('fecha_factura', models.DateField(verbose_name='Fecha de Factura')),
                ('fecha_carga', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Carga')),
                ('registro', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='facturas',
                    to='contabilidad.registrocontable',
                    verbose_name='Registro Contable',
                )),
            ],
            options={
                'verbose_name': 'Factura',
                'verbose_name_plural': 'Facturas',
                'db_table': 'contabilidad_facturas',
                'ordering': ['fecha_carga'],
            },
        ),
        migrations.CreateModel(
            name='VerificacionChecklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(
                    choices=[('PENDIENTE', 'Pendiente'), ('OK', 'OK'), ('NO_OK', 'No OK'), ('NA', 'No Aplica')],
                    default='PENDIENTE',
                    max_length=10,
                    verbose_name='Estado',
                )),
                ('observacion', models.TextField(blank=True, verbose_name='Observación')),
                ('fecha_verificacion', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Verificación')),
                ('item', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='contabilidad.itemchecklist',
                    verbose_name='Ítem de Checklist',
                )),
                ('registro', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='verificaciones',
                    to='contabilidad.registrocontable',
                    verbose_name='Registro Contable',
                )),
                ('verificado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='verificaciones_checklist',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Verificado Por',
                )),
            ],
            options={
                'verbose_name': 'Verificación Checklist',
                'verbose_name_plural': 'Verificaciones Checklist',
                'db_table': 'contabilidad_verificaciones',
            },
        ),
        migrations.AddConstraint(
            model_name='verificacionchecklist',
            constraint=models.UniqueConstraint(
                fields=['registro', 'item'],
                name='unique_registro_item',
            ),
        ),
        migrations.CreateModel(
            name='HistorialEstado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(
                    choices=[
                        ('CREACION', 'Creación'),
                        ('ENVIO', 'Envío'),
                        ('CONFIRMACION_RECEPCION', 'Confirmación de Recepción'),
                        ('DEVOLUCION_COMPRAS', 'Devolución por Compras'),
                        ('REENVIO', 'Reenvío'),
                        ('CONFIRMACION_REENTREGA', 'Confirmación de Reentrega'),
                        ('APROBACION_COMPRAS', 'Aprobación por Compras'),
                        ('INICIO_REVISION_CONTABILIDAD', 'Inicio Revisión Contabilidad'),
                        ('OBSERVACION_CONTABILIDAD', 'Observación de Contabilidad'),
                        ('RESPUESTA_COMPRAS', 'Respuesta de Compras a Observación'),
                        ('APROBACION_CONTABILIDAD', 'Aprobación por Contabilidad'),
                        ('CIERRE', 'Cierre'),
                    ],
                    max_length=40,
                    verbose_name='Acción',
                )),
                ('estado_anterior', models.CharField(blank=True, max_length=30, verbose_name='Estado Anterior')),
                ('estado_nuevo', models.CharField(blank=True, max_length=30, verbose_name='Estado Nuevo')),
                ('comentario', models.TextField(blank=True, verbose_name='Comentario')),
                ('fecha', models.DateTimeField(auto_now_add=True, verbose_name='Fecha')),
                ('registro', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='historial',
                    to='contabilidad.registrocontable',
                    verbose_name='Registro Contable',
                )),
                ('usuario', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='historial_contabilidad',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                )),
            ],
            options={
                'verbose_name': 'Historial de Estado',
                'verbose_name_plural': 'Historial de Estados',
                'db_table': 'contabilidad_historial',
                'ordering': ['fecha'],
                'indexes': [
                    models.Index(fields=['registro', 'fecha'], name='contabilida_registr_h_idx'),
                ],
            },
        ),
    ]
