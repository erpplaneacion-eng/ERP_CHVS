from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0003_registroactividad'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MunicipioModalidades',
        ),
    ]
