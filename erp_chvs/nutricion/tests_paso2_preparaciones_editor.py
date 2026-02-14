import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo, PrincipalMunicipio, TablaGradosEscolaresUapa

from .models import (
    ComponentesAlimentos,
    GruposAlimentos,
    MinutaPatronMeta,
    TablaAlimentos2018Icbf,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    TablaIngredientesSiesa,
    TablaMenus,
    TablaPreparacionIngredientes,
    TablaPreparaciones,
    TablaRequerimientosNutricionales,
)


class Paso2PreparacionesEditorIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="paso2_user", password="testpass123")
        cls.client = Client()

        cls.nivel_prescolar = TablaGradosEscolaresUapa.objects.create(
            id_grado_escolar_uapa="prescolar",
            nivel_escolar_uapa="Preescolar",
        )
        cls.nivel_primaria = TablaGradosEscolaresUapa.objects.create(
            id_grado_escolar_uapa="primaria",
            nivel_escolar_uapa="Primaria 1-3",
        )

        cls.modalidad = ModalidadesDeConsumo.objects.create(
            id_modalidades="modpaso2",
            modalidad="CAJM AM",
            cod_modalidad="CAJM",
        )
        cls.municipio = PrincipalMunicipio.objects.create(
            codigo_municipio=11111,
            nombre_municipio="Municipio Paso2",
            codigo_departamento="11",
        )
        cls.programa = Programa.objects.create(
            programa="Programa Paso2",
            contrato="CT-P2-001",
            municipio=cls.municipio,
            fecha_inicial=date(2025, 1, 1),
            fecha_final=date(2025, 12, 31),
            estado="activo",
        )
        cls.menu = TablaMenus.objects.create(
            menu="Menu Paso2",
            id_modalidad=cls.modalidad,
            id_contrato=cls.programa,
        )

        cls.grupo = GruposAlimentos.objects.create(
            id_grupo_alimentos="grp_p2",
            grupo_alimentos="Lacteos",
        )
        cls.componente = ComponentesAlimentos.objects.create(
            id_componente="comp_p2",
            componente="Bebida con leche",
            id_grupo_alimentos=cls.grupo,
        )

        cls.alimento_icbf = TablaAlimentos2018Icbf.objects.create(
            codigo="A001",
            nombre_del_alimento="Leche entera",
            humedad_g=Decimal("87.00"),
            energia_kcal=60,
            energia_kj=251,
            proteina_g=Decimal("3.20"),
            lipidos_g=Decimal("3.30"),
            carbohidratos_totales_g=Decimal("4.80"),
            calcio_mg=120,
            hierro_mg=Decimal("0.10"),
            sodio_mg=50,
            parte_comestible_field=100,
            id_componente=cls.componente,
        )
        cls.ingrediente_siesa = TablaIngredientesSiesa.objects.create(
            id_ingrediente_siesa="A001",
            nombre_ingrediente="Leche entera",
        )

        cls.preparacion = TablaPreparaciones.objects.create(
            preparacion="Leche preparada",
            id_menu=cls.menu,
            id_componente=cls.componente,
        )
        TablaPreparacionIngredientes.objects.create(
            id_preparacion=cls.preparacion,
            id_ingrediente_siesa=cls.alimento_icbf,
            gramaje=Decimal("100.00"),
        )

        MinutaPatronMeta.objects.create(
            id_modalidad=cls.modalidad,
            id_grado_escolar_uapa=cls.nivel_prescolar,
            id_componente=cls.componente,
            id_grupo_alimentos=cls.grupo,
            peso_neto_minimo=Decimal("120.00"),
            peso_neto_maximo=Decimal("160.00"),
        )
        MinutaPatronMeta.objects.create(
            id_modalidad=cls.modalidad,
            id_grado_escolar_uapa=cls.nivel_primaria,
            id_componente=cls.componente,
            id_grupo_alimentos=cls.grupo,
            peso_neto_minimo=Decimal("180.00"),
            peso_neto_maximo=Decimal("220.00"),
        )

        for nivel in [cls.nivel_prescolar, cls.nivel_primaria]:
            TablaRequerimientosNutricionales.objects.create(
                id_requerimiento_nutricional=f"req_{nivel.id_grado_escolar_uapa}",
                calorias_kcal=Decimal("276.0"),
                proteina_g=Decimal("9.9"),
                grasa_g=Decimal("9.6"),
                cho_g=Decimal("36.5"),
                calcio_mg=Decimal("159.0"),
                hierro_mg=Decimal("1.5"),
                sodio_mg=Decimal("95.0"),
                id_nivel_escolar_uapa=nivel,
                id_modalidad=cls.modalidad,
            )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_vista_preparaciones_editor_crea_analisis_por_nivel_y_aplica_rangos_por_nivel(self):
        self.assertEqual(TablaAnalisisNutricionalMenu.objects.filter(id_menu=self.menu).count(), 0)

        url = reverse("nutricion:preparaciones_editor", args=[self.menu.id_menu])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        niveles_data = response.context["niveles_data"]
        self.assertEqual(len(niveles_data), 2)

        analisis_count = TablaAnalisisNutricionalMenu.objects.filter(id_menu=self.menu).count()
        self.assertEqual(analisis_count, 2)

        data_por_nivel = {n["nivel"]["id"]: n for n in niveles_data}
        for nivel_id in ["prescolar", "primaria"]:
            self.assertIn(nivel_id, data_por_nivel)
            self.assertIn("filas", data_por_nivel[nivel_id])
            self.assertIn("totales", data_por_nivel[nivel_id])
            self.assertIn("requerimientos", data_por_nivel[nivel_id])
            self.assertIn("porcentajes", data_por_nivel[nivel_id])
            self.assertIn("estados", data_por_nivel[nivel_id])
            self.assertIn("id_analisis", data_por_nivel[nivel_id])

        fila_prescolar = data_por_nivel["prescolar"]["filas"][0]
        fila_primaria = data_por_nivel["primaria"]["filas"][0]
        self.assertEqual(fila_prescolar["minimo"], 120.0)
        self.assertEqual(fila_prescolar["maximo"], 160.0)
        self.assertEqual(fila_primaria["minimo"], 180.0)
        self.assertEqual(fila_primaria["maximo"], 220.0)

    def test_api_guardar_ingredientes_por_nivel_guarda_registros_y_recalcula_totales(self):
        analisis = TablaAnalisisNutricionalMenu.objects.create(
            id_menu=self.menu,
            id_nivel_escolar_uapa=self.nivel_prescolar,
        )

        url = reverse("nutricion:api_guardar_ingredientes_por_nivel", args=[self.menu.id_menu])
        payload = {
            "niveles": [
                {
                    "id_nivel_escolar": self.nivel_prescolar.id_grado_escolar_uapa,
                    "id_analisis": analisis.id_analisis,
                    "ingredientes": [
                        {
                            "id_preparacion": self.preparacion.id_preparacion,
                            "id_ingrediente": self.alimento_icbf.codigo,
                            "peso_neto": 150.0,
                        }
                    ],
                }
            ]
        }
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["registros_actualizados"], 1)
        self.assertEqual(body["errores"], [])

        registro = TablaIngredientesPorNivel.objects.get(
            id_analisis=analisis,
            id_preparacion=self.preparacion,
            id_ingrediente_siesa=self.ingrediente_siesa,
        )
        self.assertAlmostEqual(float(registro.peso_neto), 150.0, places=1)
        self.assertAlmostEqual(float(registro.calorias), 90.0, places=1)

        analisis.refresh_from_db()
        self.assertAlmostEqual(float(analisis.total_calorias), 90.0, places=1)
        self.assertGreater(float(analisis.total_proteina), 0.0)

    def test_api_guardar_ingredientes_por_nivel_rechaza_metodo_get(self):
        url = reverse("nutricion:api_guardar_ingredientes_por_nivel", args=[self.menu.id_menu])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_api_guardar_ingredientes_por_nivel_valida_payload_vacio(self):
        url = reverse("nutricion:api_guardar_ingredientes_por_nivel", args=[self.menu.id_menu])
        response = self.client.post(url, data=json.dumps({}), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_api_guardar_ingredientes_por_nivel_reporta_analisis_no_encontrado(self):
        url = reverse("nutricion:api_guardar_ingredientes_por_nivel", args=[self.menu.id_menu])
        payload = {
            "niveles": [
                {
                    "id_nivel_escolar": self.nivel_prescolar.id_grado_escolar_uapa,
                    "id_analisis": 999999,
                    "ingredientes": [
                        {
                            "id_preparacion": self.preparacion.id_preparacion,
                            "id_ingrediente": self.alimento_icbf.codigo,
                            "peso_neto": 140.0,
                        }
                    ],
                }
            ]
        }
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["registros_actualizados"], 0)
        self.assertTrue(any("no encontrado" in err.lower() for err in body["errores"]))

    def test_paso4_template_incluye_slider_y_labels_de_rango(self):
        url = reverse("nutricion:preparaciones_editor", args=[self.menu.id_menu])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="slider-peso"', html=False)
        self.assertContains(response, 'class="slider-label-min"', html=False)
        self.assertContains(response, 'class="slider-label-max"', html=False)
        self.assertContains(response, 'data-minimo="', html=False)
        self.assertContains(response, 'data-maximo="', html=False)

        niveles_data = response.context["niveles_data"]
        fila_prescolar = next(n for n in niveles_data if n["nivel"]["id"] == "prescolar")["filas"][0]
        self.assertEqual(fila_prescolar["minimo"], 120.0)
        self.assertEqual(fila_prescolar["maximo"], 160.0)

    def test_paso4_template_incluye_tooltips_y_data_nutricional(self):
        url = reverse("nutricion:preparaciones_editor", args=[self.menu.id_menu])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-bs-toggle="tooltip"', html=False)
        self.assertContains(response, 'class="input-peso"', html=False)
        self.assertContains(response, 'data-calorias="', html=False)
        self.assertContains(response, 'data-proteina="', html=False)
        self.assertContains(response, 'title="Calor', html=False)

    def test_paso5_template_incluye_toolbar_de_optimizacion_por_nivel(self):
        url = reverse("nutricion:preparaciones_editor", args=[self.menu.id_menu])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="btn btn-outline-primary btn-sm btn-copiar-pesos"', html=False)
        self.assertContains(response, 'class="btn btn-outline-success btn-sm btn-optimizar-pesos"', html=False)
        self.assertContains(response, 'class="btn btn-outline-info btn-sm btn-comparar-minuta"', html=False)
        self.assertContains(response, 'class="btn btn-outline-secondary btn-sm btn-sugerencias"', html=False)

    def test_paso5_template_incluye_panel_sugerencias_oculto(self):
        url = reverse("nutricion:preparaciones_editor", args=[self.menu.id_menu])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="panel-sugerencias"', html=False)
        self.assertContains(response, 'style="display: none;"', html=False)
        self.assertContains(response, 'class="btn-close-sugerencias"', html=False)
        self.assertContains(response, 'class="sugerencias-content"', html=False)


class Paso4FrontendContractsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base_dir = Path(__file__).resolve().parents[1]
        js_path = base_dir / "static" / "js" / "nutricion" / "preparaciones_editor.js"
        cls.js_source = js_path.read_text(encoding="utf-8")

    def test_paso4_js_contiene_funciones_clave_de_sync_y_validacion(self):
        js = self.js_source
        self.assertIn("function sincronizarSliderConInput(row)", js)
        self.assertIn("function sincronizarInputConSlider(row)", js)
        self.assertIn("function actualizarEstadoFila(row)", js)
        self.assertIn("if (e.target.classList.contains('input-peso'))", js)
        self.assertIn("if (e.target.classList.contains('slider-peso'))", js)
        self.assertIn("badge.textContent = resultado.valido ? 'OK' : 'FUERA';", js)

    def test_paso4_js_contiene_overlay_y_uso_en_guardar_y_sincronizar(self):
        js = self.js_source
        self.assertIn("function mostrarOverlayGuardando(mensaje = 'Guardando cambios...')", js)
        self.assertIn("function ocultarOverlayGuardando()", js)
        self.assertIn("const overlay = mostrarOverlayGuardando('Guardando cambios...');", js)
        self.assertIn(
            "const overlay = mostrarOverlayGuardando('Sincronizando pesos en todos los niveles...');",
            js,
        )
        self.assertIn("ocultarOverlayGuardando();", js)

    def test_paso5_js_contiene_funciones_auxiliares_de_optimizacion(self):
        js = self.js_source
        self.assertIn("async function copiarPesosAOtrosNiveles(nivelOrigenId)", js)
        self.assertIn("function generarSugerencias(nivelId)", js)
        self.assertIn("function mostrarSugerencias(nivelId)", js)
        self.assertIn("function ocultarSugerencias(nivelId)", js)
        self.assertIn("async function compararConMinutaPatron(nivelId)", js)

    def test_paso5_js_contiene_event_delegation_y_placeholder_optimizacion(self):
        js = self.js_source
        self.assertIn("if (e.target.closest('.btn-copiar-pesos'))", js)
        self.assertIn("if (e.target.closest('.btn-sugerencias'))", js)
        self.assertIn("if (e.target.closest('.btn-comparar-minuta'))", js)
        self.assertIn("if (e.target.closest('.btn-optimizar-pesos'))", js)
        self.assertIn("Función en desarrollo", js)
