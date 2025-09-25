# facturacion/tests.py
# -*- coding: utf-8 -*-
"""
Tests básicos para el módulo de facturación refactorizado.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

class BasicTestCase(TestCase):
    """Tests básicos para verificar que la refactorización funciona."""
    
    def test_imports_funcionan(self):
        """Test para verificar que todos los imports funcionan correctamente."""
        try:
            from .excel_utils import ExcelProcessor
            from .fuzzy_matching import FuzzyMatcher
            from .validators import DataValidator
            from .services import ProcesamientoService
            from .config import ProcesamientoConfig
            from .exceptions import FacturacionException
            from .logging_config import FacturacionLogger
        except ImportError as e:
            self.fail(f"Error de importación: {e}")
    
    def test_clases_instanciables(self):
        """Test para verificar que las clases principales son instanciables."""
        try:
            from .excel_utils import ExcelProcessor
            from .fuzzy_matching import FuzzyMatcher
            from .validators import DataValidator
            from .services import ProcesamientoService
            
            ExcelProcessor()
            FuzzyMatcher()
            DataValidator()
            ProcesamientoService()
        except Exception as e:
            self.fail(f"Error al instanciar clases: {e}")
    
    def test_config_constantes(self):
        """Test para verificar que las constantes de configuración están definidas."""
        from .config import ProcesamientoConfig
        
        self.assertIsNotNone(ProcesamientoConfig.UMBRAL_COINCIDENCIA_DIFUSA)
        self.assertIsNotNone(ProcesamientoConfig.COLUMNAS_NUEVO_FORMATO)
        self.assertIsNotNone(ProcesamientoConfig.COLUMNAS_ORIGINAL_FORMATO)
        self.assertIsNotNone(ProcesamientoConfig.MUNICIPIOS_SOPORTADOS)
    
    def test_fuzzy_matcher_normalizacion(self):
        """Test básico para normalización de texto."""
        from .fuzzy_matching import FuzzyMatcher
        
        matcher = FuzzyMatcher()
        resultado = matcher.normalizar_texto("  INSTITUCIÓN EDUCATIVA  ")
        esperado = "institucion educativa"
        self.assertEqual(resultado, esperado)
