# Generated manually for OCR refactorization
# Date: 2025-01-06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr_validation', '0004_pdfvalidation_datos_estructurados_and_more'),
    ]

    operations = [
        # Eliminar campo antiguo tesseract_config
        migrations.RemoveField(
            model_name='ocrconfiguration',
            name='tesseract_config',
        ),

        # Agregar nuevo campo modelo_landingai
        migrations.AddField(
            model_name='ocrconfiguration',
            name='modelo_landingai',
            field=models.CharField(
                default='dpt-2-latest',
                max_length=50,
                verbose_name='Modelo LandingAI'
            ),
        ),

        # Actualizar valor por defecto de confianza_minima
        migrations.AlterField(
            model_name='ocrconfiguration',
            name='confianza_minima',
            field=models.FloatField(
                default=90.0,
                verbose_name='Confianza Mínima Extracción (%)'
            ),
        ),
    ]
