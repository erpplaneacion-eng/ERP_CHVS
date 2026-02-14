"""
Tests para la sincronización de pesos entre preparaciones y análisis nutricional.

Ejecutar:
    python manage.py test nutricion.tests_sincronizacion_pesos

o con pytest:
    pytest nutricion/tests_sincronizacion_pesos.py -v
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.contrib.auth.models import User
import json

from .models import (
    TablaMenus,
    TablaPreparaciones,
    TablaPreparacionIngredientes,
    TablaAlimentos2018Icbf,
    TablaIngredientesSiesa,
    TablaIngredientesPorNivel,
    TablaAnalisisNutricionalMenu,
    TablaRequerimientosNutricionales,
    ComponentesAlimentos,
    GruposAlimentos
)
from .services import AnalisisNutricionalService
from principal.models import (
    ModalidadesDeConsumo,
    TablaGradosEscolaresUapa
)
from planeacion.models import Programa, PrincipalMunicipio


class SincronizacionPesosTestCase(TestCase):
    """
    Tests para verificar la sincronización de pesos desde preparaciones
    hacia análisis nutricional.
    """

    @classmethod
    def setUpTestData(cls):
        """Configurar datos de prueba que se usan en todos los tests."""

        # Crear usuario de prueba
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Crear nivel escolar
        cls.nivel_escolar = TablaGradosEscolaresUapa.objects.create(
            id_grado_escolar_uapa='prescolar',
            nivel_escolar_uapa='Preescolar'
        )

        # Crear modalidad
        cls.modalidad = ModalidadesDeConsumo.objects.create(
            id_modalidades='mod_test',
            modalidad='CAJM AM Test'
        )

        # Crear municipio
        cls.municipio = PrincipalMunicipio.objects.create(
            codigo_municipio=99999,
            nombre_municipio='Municipio Test',
            codigo_departamento='99'
        )

        # Crear programa
        cls.programa = Programa.objects.create(
            programa='Programa Test',
            contrato='CT-001',
            municipio=cls.municipio,
            fecha_inicial=date(2025, 1, 1),
            fecha_final=date(2025, 12, 31),
            estado='activo'
        )

        # Crear menú
        cls.menu = TablaMenus.objects.create(
            menu='Menú Test 1',
            id_modalidad=cls.modalidad,
            id_contrato=cls.programa
        )

        # Crear grupo de alimentos
        cls.grupo_alimentos = GruposAlimentos.objects.create(
            id_grupo_alimentos='grp_test',
            grupo_alimentos='Lácteos Test'
        )

        # Crear componente
        cls.componente = ComponentesAlimentos.objects.create(
            id_componente='comp_test',
            componente='Bebida con leche Test',
            id_grupo_alimentos=cls.grupo_alimentos
        )

        # Crear alimentos ICBF de prueba
        cls.alimento1 = TablaAlimentos2018Icbf.objects.create(
            codigo='A001',
            nombre_del_alimento='Leche entera',
            humedad_g=Decimal('87.0'),
            energia_kcal=60,
            energia_kj=251,
            proteina_g=Decimal('3.2'),
            lipidos_g=Decimal('3.3'),
            carbohidratos_totales_g=Decimal('4.8'),
            calcio_mg=120,
            hierro_mg=Decimal('0.1'),
            sodio_mg=50,
            parte_comestible_field=100,
            id_componente=cls.componente
        )

        cls.alimento2 = TablaAlimentos2018Icbf.objects.create(
            codigo='A002',
            nombre_del_alimento='Arroz blanco',
            humedad_g=Decimal('68.0'),
            energia_kcal=130,
            energia_kj=544,
            proteina_g=Decimal('2.7'),
            lipidos_g=Decimal('0.3'),
            carbohidratos_totales_g=Decimal('28.2'),
            calcio_mg=10,
            hierro_mg=Decimal('0.8'),
            sodio_mg=1,
            parte_comestible_field=100,
            id_componente=cls.componente
        )

        # Crear ingredientes SIESA
        cls.ingrediente_siesa1 = TablaIngredientesSiesa.objects.create(
            id_ingrediente_siesa='A001',
            nombre_ingrediente='Leche entera'
        )

        cls.ingrediente_siesa2 = TablaIngredientesSiesa.objects.create(
            id_ingrediente_siesa='A002',
            nombre_ingrediente='Arroz blanco'
        )

        # Crear preparación
        cls.preparacion = TablaPreparaciones.objects.create(
            preparacion='Arroz con leche',
            id_menu=cls.menu,
            id_componente=cls.componente
        )

        # Crear requerimiento nutricional
        cls.requerimiento = TablaRequerimientosNutricionales.objects.create(
            id_requerimiento_nutricional='req_test_1',
            calorias_kcal=Decimal('276.0'),
            proteina_g=Decimal('9.9'),
            grasa_g=Decimal('9.6'),
            cho_g=Decimal('36.5'),
            calcio_mg=Decimal('159'),
            hierro_mg=Decimal('1.5'),
            sodio_mg=Decimal('95'),
            id_nivel_escolar_uapa=cls.nivel_escolar,
            id_modalidad=cls.modalidad
        )

    def setUp(self):
        """Configurar datos que se reinician en cada test."""
        # Crear relaciones preparación-ingredientes con gramajes
        self.rel1 = TablaPreparacionIngredientes.objects.create(
            id_preparacion=self.preparacion,
            id_ingrediente_siesa=self.alimento1,
            gramaje=Decimal('150.0')  # 150g de leche
        )

        self.rel2 = TablaPreparacionIngredientes.objects.create(
            id_preparacion=self.preparacion,
            id_ingrediente_siesa=self.alimento2,
            gramaje=Decimal('80.0')  # 80g de arroz
        )

    def test_obtener_preparaciones_usa_gramaje(self):
        """
        Test: _obtener_preparaciones_con_ingredientes debe usar el gramaje guardado
        como peso inicial en lugar de 100g.
        """
        resultado = AnalisisNutricionalService._obtener_preparaciones_con_ingredientes(self.menu)

        # Verificar que retorna datos
        self.assertEqual(len(resultado), 1)
        preparacion_data = resultado[0]

        # Verificar que tiene ingredientes
        self.assertEqual(len(preparacion_data['ingredientes']), 2)

        # Verificar que usa el gramaje guardado
        ingrediente1_data = next(
            ing for ing in preparacion_data['ingredientes']
            if ing['codigo_icbf'] == 'A001'
        )
        ingrediente2_data = next(
            ing for ing in preparacion_data['ingredientes']
            if ing['codigo_icbf'] == 'A002'
        )

        # Verificar pesos
        self.assertEqual(float(ingrediente1_data['peso_neto_base']), 150.0)
        self.assertEqual(float(ingrediente2_data['peso_neto_base']), 80.0)

        print("OK Test 1: _obtener_preparaciones_con_ingredientes usa gramaje")

    def test_obtener_preparaciones_usa_100g_sin_gramaje(self):
        """
        Test: Si no hay gramaje guardado, debe usar 100g como fallback.
        """
        # Eliminar gramajes
        TablaPreparacionIngredientes.objects.all().update(gramaje=None)

        resultado = AnalisisNutricionalService._obtener_preparaciones_con_ingredientes(self.menu)

        preparacion_data = resultado[0]
        ingrediente_data = preparacion_data['ingredientes'][0]

        # Verificar que usa 100g por defecto
        self.assertEqual(float(ingrediente_data['peso_neto_base']), 100.0)

        print("OK Test 2: Usa 100g cuando no hay gramaje")

    def test_sincronizar_pesos_crea_ingredientes_por_nivel(self):
        """
        Test: sincronizar_pesos_desde_preparaciones debe crear registros
        en TablaIngredientesPorNivel.
        """
        # Sincronizar
        resultado = AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=self.menu.id_menu,
            id_nivel_escolar=self.nivel_escolar.id_grado_escolar_uapa,
            sobrescribir_existentes=True
        )

        # Verificar resultado
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['sincronizados'], 2)
        self.assertEqual(resultado['omitidos'], 0)
        self.assertEqual(len(resultado['errores']), 0)

        # Verificar que se crearon los registros
        analisis = TablaAnalisisNutricionalMenu.objects.get(
            id_menu=self.menu,
            id_nivel_escolar_uapa=self.nivel_escolar
        )

        ingredientes_nivel = TablaIngredientesPorNivel.objects.filter(
            id_analisis=analisis
        )

        self.assertEqual(ingredientes_nivel.count(), 2)

        print("OK Test 3: Sincronizacion crea registros en TablaIngredientesPorNivel")

    def test_sincronizar_pesos_calcula_valores_nutricionales(self):
        """
        Test: La sincronización debe calcular correctamente los valores nutricionales
        para los pesos específicos.
        """
        # Sincronizar
        AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=self.menu.id_menu,
            id_nivel_escolar=self.nivel_escolar.id_grado_escolar_uapa,
            sobrescribir_existentes=True
        )

        # Obtener ingrediente de leche (150g)
        analisis = TablaAnalisisNutricionalMenu.objects.get(
            id_menu=self.menu,
            id_nivel_escolar_uapa=self.nivel_escolar
        )

        ing_leche = TablaIngredientesPorNivel.objects.get(
            id_analisis=analisis,
            id_ingrediente_siesa__id_ingrediente_siesa='A001'
        )

        # Verificar peso
        self.assertEqual(float(ing_leche.peso_neto), 150.0)

        # Verificar calorías (60 Kcal/100g * 150g = 90 Kcal)
        calorias_esperadas = 60 * 150 / 100
        self.assertAlmostEqual(float(ing_leche.calorias), calorias_esperadas, places=1)

        # Verificar proteína (3.2g/100g * 150g = 4.8g)
        proteina_esperada = 3.2 * 150 / 100
        self.assertAlmostEqual(float(ing_leche.proteina), proteina_esperada, places=1)

        print("OK Test 4: Sincronizacion calcula valores nutricionales correctos")

    def test_recalcular_totales_analisis(self):
        """
        Test: _recalcular_totales_analisis debe sumar correctamente los totales.
        """
        # Sincronizar primero
        AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=self.menu.id_menu,
            id_nivel_escolar=self.nivel_escolar.id_grado_escolar_uapa,
            sobrescribir_existentes=True
        )

        # Obtener análisis
        analisis = TablaAnalisisNutricionalMenu.objects.get(
            id_menu=self.menu,
            id_nivel_escolar_uapa=self.nivel_escolar
        )

        # Calcular totales esperados
        # Leche 150g: 90 Kcal, 4.8g proteína
        # Arroz 80g: 104 Kcal, 2.16g proteína
        calorias_esperadas = (60 * 150 / 100) + (130 * 80 / 100)
        proteina_esperada = (3.2 * 150 / 100) + (2.7 * 80 / 100)

        # Verificar totales
        self.assertAlmostEqual(float(analisis.total_calorias), calorias_esperadas, places=1)
        self.assertAlmostEqual(float(analisis.total_proteina), proteina_esperada, places=1)

        # Verificar peso neto total (150g + 80g = 230g)
        self.assertAlmostEqual(float(analisis.total_peso_neto), 230.0, places=1)

        print("OK Test 5: Recalculo de totales correcto")

    def test_recalcular_porcentajes_adecuacion(self):
        """
        Test: Debe calcular correctamente los porcentajes de adecuación.
        """
        # Sincronizar
        AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=self.menu.id_menu,
            id_nivel_escolar=self.nivel_escolar.id_grado_escolar_uapa,
            sobrescribir_existentes=True
        )

        # Obtener análisis
        analisis = TablaAnalisisNutricionalMenu.objects.get(
            id_menu=self.menu,
            id_nivel_escolar_uapa=self.nivel_escolar
        )

        # Calcular porcentaje esperado de calorías
        # Total: ~194 Kcal / Requerimiento: 276 Kcal = ~70.3%
        porcentaje_esperado = (float(analisis.total_calorias) / 276.0) * 100

        self.assertAlmostEqual(
            float(analisis.porcentaje_calorias),
            porcentaje_esperado,
            places=1
        )

        print(f"OK Test 6: Porcentaje calorias = {analisis.porcentaje_calorias:.1f}%")

    def test_semaforizacion_estados(self):
        """
        Test: Debe asignar correctamente los estados de semaforización.
        """
        # Sincronizar
        AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=self.menu.id_menu,
            id_nivel_escolar=self.nivel_escolar.id_grado_escolar_uapa,
            sobrescribir_existentes=True
        )

        # Obtener análisis
        analisis = TablaAnalisisNutricionalMenu.objects.get(
            id_menu=self.menu,
            id_nivel_escolar_uapa=self.nivel_escolar
        )

        # Con ~70% de calorías, debería estar en "aceptable" o "alto"
        # (0-35% = óptimo, 35-70% = aceptable, >70% = alto)
        porcentaje_calorias = float(analisis.porcentaje_calorias)

        if porcentaje_calorias <= 35:
            estado_esperado = 'optimo'
        elif porcentaje_calorias <= 70:
            estado_esperado = 'aceptable'
        else:
            estado_esperado = 'alto'

        self.assertEqual(analisis.estado_calorias, estado_esperado)

        print(f"OK Test 7: Estado semaforizacion = {analisis.estado_calorias}")

    def test_sincronizar_no_sobrescribe_si_false(self):
        """
        Test: Si sobrescribir_existentes=False, no debe sobrescribir datos existentes.
        """
        # Sincronizar primera vez
        AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=self.menu.id_menu,
            id_nivel_escolar=self.nivel_escolar.id_grado_escolar_uapa,
            sobrescribir_existentes=True
        )

        # Cambiar gramaje
        self.rel1.gramaje = Decimal('200.0')
        self.rel1.save()

        # Sincronizar sin sobrescribir
        resultado = AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=self.menu.id_menu,
            id_nivel_escolar=self.nivel_escolar.id_grado_escolar_uapa,
            sobrescribir_existentes=False
        )

        # Verificar que omitió los existentes
        self.assertEqual(resultado['omitidos'], 2)
        self.assertEqual(resultado['sincronizados'], 0)

        # Verificar que el peso NO cambió
        analisis = TablaAnalisisNutricionalMenu.objects.get(
            id_menu=self.menu,
            id_nivel_escolar_uapa=self.nivel_escolar
        )

        ing_leche = TablaIngredientesPorNivel.objects.get(
            id_analisis=analisis,
            id_ingrediente_siesa__id_ingrediente_siesa='A001'
        )

        # Debe seguir siendo 150g, no 200g
        self.assertEqual(float(ing_leche.peso_neto), 150.0)

        print("OK Test 8: No sobrescribe si sobrescribir_existentes=False")

    def test_sincronizar_si_sobrescribe_si_true(self):
        """
        Test: Si sobrescribir_existentes=True, debe actualizar datos existentes.
        """
        # Sincronizar primera vez
        AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=self.menu.id_menu,
            id_nivel_escolar=self.nivel_escolar.id_grado_escolar_uapa,
            sobrescribir_existentes=True
        )

        # Cambiar gramaje
        self.rel1.gramaje = Decimal('200.0')
        self.rel1.save()

        # Sincronizar CON sobrescribir
        resultado = AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=self.menu.id_menu,
            id_nivel_escolar=self.nivel_escolar.id_grado_escolar_uapa,
            sobrescribir_existentes=True
        )

        # Verificar que actualizó
        self.assertEqual(resultado['sincronizados'], 2)

        # Verificar que el peso SÍ cambió
        analisis = TablaAnalisisNutricionalMenu.objects.get(
            id_menu=self.menu,
            id_nivel_escolar_uapa=self.nivel_escolar
        )

        ing_leche = TablaIngredientesPorNivel.objects.get(
            id_analisis=analisis,
            id_ingrediente_siesa__id_ingrediente_siesa='A001'
        )

        # Debe ser 200g ahora
        self.assertEqual(float(ing_leche.peso_neto), 200.0)

        print("OK Test 9: Sobrescribe si sobrescribir_existentes=True")

    def test_obtener_analisis_completo_usa_gramaje(self):
        """
        Test: obtener_analisis_completo debe usar automáticamente los gramajes guardados.
        """
        # Obtener análisis completo
        resultado = AnalisisNutricionalService.obtener_analisis_completo(self.menu.id_menu)

        # Verificar éxito
        self.assertTrue(resultado['success'])

        # Buscar el nivel de prueba
        analisis_nivel = next(
            nivel for nivel in resultado['analisis_por_nivel']
            if nivel['nivel_escolar']['id'] == self.nivel_escolar.id_grado_escolar_uapa
        )

        # Buscar la preparación
        preparacion_data = analisis_nivel['preparaciones'][0]

        # Verificar que usa los gramajes
        ing_leche = next(
            ing for ing in preparacion_data['ingredientes']
            if ing['codigo_icbf'] == 'A001'
        )

        self.assertEqual(float(ing_leche['peso_neto_base']), 150.0)

        print("OK Test 10: obtener_analisis_completo usa gramajes automaticamente")


class APIEndpointTestCase(TestCase):
    """
    Tests para el endpoint de sincronización de pesos.
    """

    def setUp(self):
        """Configurar datos de prueba."""
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()

        # Crear datos básicos (similar a SincronizacionPesosTestCase)
        self.nivel_escolar = TablaGradosEscolaresUapa.objects.create(
            id_grado_escolar_uapa='prescolar',
            nivel_escolar_uapa='Preescolar'
        )

        self.modalidad = ModalidadesDeConsumo.objects.create(
            id_modalidades='mod_test',
            modalidad='CAJM AM Test'
        )

        self.municipio = PrincipalMunicipio.objects.create(
            codigo_municipio=99999,
            nombre_municipio='Municipio Test',
            codigo_departamento='99'
        )

        self.programa = Programa.objects.create(
            programa='Programa Test',
            contrato='CT-001',
            municipio=self.municipio,
            fecha_inicial=date(2025, 1, 1),
            fecha_final=date(2025, 12, 31),
            estado='activo'
        )

        self.menu = TablaMenus.objects.create(
            menu='Menú Test',
            id_modalidad=self.modalidad,
            id_contrato=self.programa
        )

    def test_api_requiere_autenticacion(self):
        """Test: El endpoint debe requerir autenticación."""
        response = self.client.post(
            '/nutricion/api/sincronizar-pesos-preparaciones/',
            data=json.dumps({
                'id_menu': self.menu.id_menu,
                'id_nivel_escolar': 'prescolar'
            }),
            content_type='application/json'
        )

        # Debe redirigir al login (302) o denegar acceso (403)
        self.assertIn(response.status_code, [302, 403])

        print("OK Test API 1: Requiere autenticacion")

    def test_api_requiere_metodo_post(self):
        """Test: El endpoint solo acepta POST."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/nutricion/api/sincronizar-pesos-preparaciones/')

        self.assertEqual(response.status_code, 405)  # Method Not Allowed

        print("OK Test API 2: Solo acepta POST")

    def test_api_requiere_parametros(self):
        """Test: El endpoint debe validar parámetros requeridos."""
        self.client.login(username='testuser', password='testpass123')

        # Sin parámetros
        response = self.client.post(
            '/nutricion/api/sincronizar-pesos-preparaciones/',
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

        print("OK Test API 3: Valida parametros requeridos")

    def test_api_responde_correctamente(self):
        """Test: El endpoint debe responder correctamente con datos válidos."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(
            '/nutricion/api/sincronizar-pesos-preparaciones/',
            data=json.dumps({
                'id_menu': self.menu.id_menu,
                'id_nivel_escolar': 'prescolar',
                'sobrescribir_existentes': True
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertIn('sincronizados', data)
        self.assertIn('omitidos', data)

        print("OK Test API 4: Responde correctamente")


def run_tests_verbose():
    """
    Función auxiliar para ejecutar los tests con output detallado.
    """
    import sys
    from io import StringIO
    from django.test.runner import DiscoverRunner

    # Capturar output
    test_runner = DiscoverRunner(verbosity=2)

    # Ejecutar tests
    failures = test_runner.run_tests(['nutricion.tests_sincronizacion_pesos'])

    if failures:
        print(f"\nERROR: {failures} test(s) fallaron")
        sys.exit(1)
    else:
        print("\nOK: Todos los tests pasaron exitosamente")
        sys.exit(0)


if __name__ == '__main__':
    run_tests_verbose()
