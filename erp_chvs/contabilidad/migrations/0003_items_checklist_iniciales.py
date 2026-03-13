from django.db import migrations


ITEMS = [
    # (nombre, descripcion, tipo_proceso, obligatorio, orden)

    # ── AMBOS ──────────────────────────────────────────────────────────────
    ("Factura original con firma del proveedor",
     "La factura debe estar firmada y sellada por el proveedor.",
     "AMBOS", True, 10),

    ("Factura con número de resolución DIAN",
     "Verificar que la factura tenga el número de resolución DIAN vigente.",
     "AMBOS", True, 20),

    ("Orden de compra asociada",
     "Debe existir una orden de compra aprobada que ampare la factura.",
     "AMBOS", True, 30),

    ("RUT del proveedor",
     "Copia del RUT actualizado del proveedor.",
     "AMBOS", False, 40),

    ("Datos bancarios del proveedor",
     "Certificación bancaria vigente (no mayor a 30 días) del proveedor.",
     "AMBOS", False, 50),

    # ── SERVICIOS ──────────────────────────────────────────────────────────
    ("Acta de recibo conforme de servicios",
     "Documento firmado por el responsable del área que certifica que el servicio fue prestado satisfactoriamente.",
     "SERVICIOS", True, 60),

    ("Informe o entregable del servicio",
     "Soporte técnico, informe o evidencia del servicio prestado según contrato.",
     "SERVICIOS", True, 70),

    ("Certificado de cumplimiento del contrato",
     "Certificación emitida por el supervisor del contrato.",
     "SERVICIOS", False, 80),

    # ── MATERIAS_PRIMAS ────────────────────────────────────────────────────
    ("Entrada al almacén (remisión firmada)",
     "Remisión o nota de entrega firmada por el almacenista que confirma la recepción física de la mercancía.",
     "MATERIAS_PRIMAS", True, 60),

    ("Acta de recibo conforme de materias primas",
     "Documento firmado por el responsable de almacén que certifica calidad y cantidad recibida.",
     "MATERIAS_PRIMAS", True, 70),

    ("Guía de transporte / remesa",
     "Documento de transporte que acompaña el despacho de la mercancía.",
     "MATERIAS_PRIMAS", False, 80),

    ("Certificado de calidad o análisis del producto",
     "Certificado del fabricante o laboratorio que avala la calidad de las materias primas.",
     "MATERIAS_PRIMAS", False, 90),
]


def insertar_items(apps, schema_editor):
    ItemChecklist = apps.get_model('contabilidad', 'ItemChecklist')
    for nombre, descripcion, tipo_proceso, obligatorio, orden in ITEMS:
        ItemChecklist.objects.get_or_create(
            nombre=nombre,
            defaults={
                'descripcion': descripcion,
                'tipo_proceso': tipo_proceso,
                'obligatorio': obligatorio,
                'activo': True,
                'orden': orden,
            }
        )


def eliminar_items(apps, schema_editor):
    ItemChecklist = apps.get_model('contabilidad', 'ItemChecklist')
    nombres = [i[0] for i in ITEMS]
    ItemChecklist.objects.filter(nombre__in=nombres).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0002_remove_verificacionchecklist_unique_registro_item_and_more'),
    ]

    operations = [
        migrations.RunPython(insertar_items, eliminar_items),
    ]
