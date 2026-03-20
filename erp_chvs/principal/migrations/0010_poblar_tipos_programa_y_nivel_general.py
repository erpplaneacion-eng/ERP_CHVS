from django.db import migrations


def poblar_tipos_programa(apps, schema_editor):
    TipoPrograma = apps.get_model('principal', 'TipoPrograma')
    tipos = [
        {
            'id_tipo_programa': 'pae',
            'nombre': 'Programa de Alimentación Escolar',
            'tiene_niveles': True,
            'descripcion': 'PAE - niveles escolares ICBF',
        },
        {
            'id_tipo_programa': 'adulto_mayor',
            'nombre': 'Atención al Adulto Mayor',
            'tiene_niveles': False,
            'descripcion': 'Comedores para adultos mayores',
        },
        {
            'id_tipo_programa': 'comedores_comunitarios',
            'nombre': 'Comedores Comunitarios',
            'tiene_niveles': False,
            'descripcion': 'Comedores comunitarios',
        },
    ]
    for t in tipos:
        TipoPrograma.objects.get_or_create(
            id_tipo_programa=t['id_tipo_programa'],
            defaults=t,
        )


def poblar_nivel_general(apps, schema_editor):
    TablaGradosEscolaresUapa = apps.get_model('principal', 'TablaGradosEscolaresUapa')
    TablaGradosEscolaresUapa.objects.get_or_create(
        id_grado_escolar_uapa='general',
        defaults={'nivel_escolar_uapa': 'General (sin niveles)'},
    )


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0009_add_tipo_programa'),
    ]

    operations = [
        migrations.RunPython(poblar_tipos_programa, revertir),
        migrations.RunPython(poblar_nivel_general, revertir),
    ]
