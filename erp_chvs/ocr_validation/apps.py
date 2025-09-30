from django.apps import AppConfig


class OcrValidationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ocr_validation'
    verbose_name = 'Validación OCR'

    def ready(self):
        # Importar señales si las tienes
        pass