from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import PDFValidation, ValidationError, OCRConfiguration
from .ocr_service import OCRProcessor, OCRValidator
from .exceptions import OCRProcessingException

class OCRValidationTests(TestCase):
    """Pruebas para el módulo de validación OCR."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Crear configuración OCR por defecto
        self.config = OCRConfiguration.objects.create(
            confianza_minima=60.0,
            detectar_firmas=True
        )

    def test_crear_registro_validacion(self):
        """Prueba creación de registro de validación."""
        # Crear archivo PDF simulado
        pdf_content = b'%PDF-1.4\n%test pdf content'
        archivo_pdf = SimpleUploadedFile(
            "test_asistencia.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        procesador = OCRProcessor()
        registro = procesador._crear_registro_validacion(archivo_pdf)

        self.assertIsInstance(registro, PDFValidation)
        self.assertEqual(registro.archivo_nombre, "test_asistencia.pdf")
        self.assertEqual(registro.estado, 'procesando')

    def test_parsear_nombre_archivo(self):
        """Prueba análisis de nombre de archivo."""
        procesador = OCRProcessor()

        # Probar nombre de archivo típico
        nombre = "Asistencia_Sede_Educativa_CAJMPS_OCTUBRE_2025.pdf"
        info = procesador._parsear_nombre_archivo(nombre)

        self.assertEqual(info['sede'], 'Sede_Educativa')
        self.assertEqual(info['complemento'], 'CAJMPS')
        self.assertEqual(info['mes'], 'OCTUBRE')
        self.assertEqual(info['ano'], '2025')

    def test_validacion_campos_numericos(self):
        """Prueba validación de campos numéricos."""
        validador = OCRValidator()

        # Probar campo numérico válido
        errores = validador._validar_campo_numerico("150", {
            'tipo': 'numero',
            'obligatorio': True,
            'patron': r'^\d+$',
            'valor_minimo': '0',
            'valor_maximo': '1000'
        })

        # No debería haber errores
        self.assertEqual(len(errores), 0)

    def test_validacion_firmas(self):
        """Prueba validación de firmas."""
        validador = OCRValidator()

        # Probar firma válida
        errores = validador._validar_campo_firma("Juan Pérez García", {
            'tipo': 'firma',
            'obligatorio': True
        })

        # No debería haber errores críticos
        errores_criticos = [e for e in errores if e['severidad'] == 'critico']
        self.assertEqual(len(errores_criticos), 0)

    def test_validacion_celdas_x(self):
        """Prueba validación de celdas con X."""
        validador = OCRValidator()

        # Probar celda con X válida
        errores = validador._validar_campo_celda_x("   X   ", {
            'tipo': 'celda_x',
            'obligatorio': True
        })

        # No debería haber errores de posición
        errores_posicion = [e for e in errores if e['tipo'] == 'posicion_x_incorrecta']
        self.assertEqual(len(errores_posicion), 0)

    def test_modelo_pdf_validation(self):
        """Prueba modelo PDFValidation."""
        validacion = PDFValidation.objects.create(
            archivo_nombre="test.pdf",
            sede_educativa="Sede Test",
            mes_atencion="OCTUBRE",
            ano=2025,
            tipo_complemento="CAJMPS",
            estado="completado",
            total_errores=2,
            errores_criticos=1,
            errores_advertencia=1
        )

        self.assertEqual(validacion.total_errores, 2)
        self.assertEqual(validacion.errores_criticos, 1)
        self.assertEqual(str(validacion), "Validación Sede Test - OCTUBRE/2025")

    def test_modelo_validation_error(self):
        """Prueba modelo ValidationError."""
        validacion = PDFValidation.objects.create(
            archivo_nombre="test.pdf",
            sede_educativa="Sede Test",
            mes_atencion="OCTUBRE",
            ano=2025,
            tipo_complemento="CAJMPS"
        )

        error = ValidationError.objects.create(
            validacion=validacion,
            tipo_error="campo_vacio",
            descripcion="Campo obligatorio vacío",
            pagina=1,
            severidad="critico"
        )

        self.assertEqual(error.severidad, "critico")
        self.assertFalse(error.resuelto)
        self.assertEqual(str(error), "campo_vacio: Campo obligatorio vacío")