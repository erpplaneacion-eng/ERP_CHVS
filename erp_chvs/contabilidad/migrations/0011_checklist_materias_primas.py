from django.db import migrations, models


def crear_items_materias_primas(apps, schema_editor):
    ItemChecklist = apps.get_model('contabilidad', 'ItemChecklist')

    # Desactivar ítems placeholder actuales de MATERIAS_PRIMAS
    ItemChecklist.objects.filter(tipo_proceso='MATERIAS_PRIMAS').update(activo=False)

    # 4 ítems básicos (toda factura MATERIAS_PRIMAS)
    basicos = [
        (10, 'NIT de la empresa (Corporación Hacia un Valle Solidario)'),
        (20, 'Fecha de facturación'),
        (30, 'Estado físico de la factura (sin tachones, enmendaduras ni hoja arrugada)'),
        (40, 'Firma del personal responsable de logística'),
    ]
    for orden, nombre in basicos:
        obj, created = ItemChecklist.objects.get_or_create(
            nombre=nombre,
            tipo_proceso='MATERIAS_PRIMAS',
            defaults={
                'obligatorio': True,
                'activo': True,
                'orden': orden,
                'es_formato_devolucion': False,
            }
        )
        if not created:
            obj.activo = True
            obj.orden = orden
            obj.obligatorio = True
            obj.es_formato_devolucion = False
            obj.save()

    # 5 ítems condicionales (solo cuando la factura tiene formato de devolución)
    formato_dev = [
        (50, 'Firma de quien recibe la mercancía'),
        (60, 'Cantidad de mercancía'),
        (70, 'Número de factura en formato de devolución'),
        (80, 'Firma de quien entrega (conductor)'),
        (90, 'Firma de quien recibe en destino (conductor)'),
    ]
    for orden, nombre in formato_dev:
        obj, created = ItemChecklist.objects.get_or_create(
            nombre=nombre,
            tipo_proceso='MATERIAS_PRIMAS',
            defaults={
                'obligatorio': True,
                'activo': True,
                'orden': orden,
                'es_formato_devolucion': True,
            }
        )
        if not created:
            obj.activo = True
            obj.orden = orden
            obj.obligatorio = True
            obj.es_formato_devolucion = True
            obj.save()


def revertir_items_materias_primas(apps, schema_editor):
    # Reversión: solo reactivar los que estaban antes (no podemos saber cuáles eran)
    # Se deja vacío — la migración no se puede revertir de forma segura con datos.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0010_add_estado_contabilidad_to_factura'),
    ]

    operations = [
        # Parte A: Schema
        migrations.AddField(
            model_name='factura',
            name='tiene_formato_devolucion',
            field=models.BooleanField(
                default=False,
                help_text='Indica si esta factura acompaña un formato físico de devolución de mercancía.',
                verbose_name='Tiene Formato de Devolución',
            ),
        ),
        migrations.AddField(
            model_name='itemchecklist',
            name='es_formato_devolucion',
            field=models.BooleanField(
                default=False,
                help_text='Si True, este ítem solo aplica a facturas con formato de devolución.',
                verbose_name='Es ítem de Formato Devolución',
            ),
        ),
        # Parte B: Datos
        migrations.RunPython(
            crear_items_materias_primas,
            revertir_items_materias_primas,
        ),
    ]
