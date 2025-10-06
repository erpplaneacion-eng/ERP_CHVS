# Generated migration for adding metodo_ocr field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr_validation', '0002_pdfvalidation_usuario_creador'),
    ]

    operations = [
        migrations.AddField(
            model_name='pdfvalidation',
            name='metodo_ocr',
            field=models.CharField(
                choices=[
                    ('tesseract', 'Tesseract OCR'),
                    ('landingai', 'LandingAI ADE')
                ],
                default='tesseract',
                max_length=20,
                verbose_name='Método OCR'
            ),
        ),
    ]
