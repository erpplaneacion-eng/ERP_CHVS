# Generated manually to fix municipio ID sequence

from django.db import migrations


def fix_municipio_sequence(apps, schema_editor):
    """Fix the municipio ID sequence to start from the correct value"""
    from django.db import connection

    with connection.cursor() as cursor:
        # Obtener el ID más alto
        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM principal_municipio;")
        max_id = cursor.fetchone()[0]

        # Resetear la secuencia
        cursor.execute(f"SELECT setval(pg_get_serial_sequence('principal_municipio', 'id'), {max_id}, false);")

        print(f"Secuencia de municipios ajustada al valor: {max_id}")


def reverse_fix_municipio_sequence(apps, schema_editor):
    """Reverse operation - nothing to do"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0005_alter_principalmunicipio_options'),
    ]

    operations = [
        migrations.RunPython(fix_municipio_sequence, reverse_fix_municipio_sequence),
    ]