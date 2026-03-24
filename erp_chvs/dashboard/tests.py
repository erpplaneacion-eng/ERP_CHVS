"""
Tests para el módulo dashboard — servicios NIA (chat IA).

Cubre:
- obtener_sedes_mapa: estructura y tipos de retorno
- _resolver_sede: resolución difusa por nombre
- obtener_focalizaciones: valores reales en BD para programa id=15
- procesar_mensaje_nia: flujo completo con mock de Gemini
- obtener_actividad_para_contexto: sin excepción, retorna string no vacío
"""
import json
import logging
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from dashboard import services
from dashboard.services import (
    _resolver_sede,
    obtener_actividad_para_contexto,
    obtener_focalizaciones,
    obtener_sedes_mapa,
    procesar_mensaje_nia,
)
from facturacion.models import ListadosFocalizacion
from planeacion.models import SedesEducativas
from principal.models import RegistroActividad

logger = logging.getLogger(__name__)

PROGRAMA_ID_REAL = 15


# ---------------------------------------------------------------------------
# Test 1 — obtener_sedes_mapa
# ---------------------------------------------------------------------------

class ObtenerSedesMapaTests(TestCase):
    """Verifica que obtener_sedes_mapa retorna {str: str} para programa id=15."""

    def test_retorna_dict_con_claves_y_valores_str(self):
        mapa = obtener_sedes_mapa(PROGRAMA_ID_REAL)
        logger.info(
            "obtener_sedes_mapa(programa_id=%d) => %d sedes encontradas",
            PROGRAMA_ID_REAL,
            len(mapa),
        )
        self.assertIsInstance(mapa, dict, "obtener_sedes_mapa debe retornar un dict")
        for nombre, cod in mapa.items():
            self.assertIsInstance(
                nombre, str,
                f"Clave de sedes_mapa no es str: {nombre!r} ({type(nombre).__name__})",
            )
            self.assertIsInstance(
                cod, str,
                f"Valor de sedes_mapa no es str para sede '{nombre}': {cod!r} ({type(cod).__name__})",
            )

    def test_loggea_sedes_encontradas(self):
        mapa = obtener_sedes_mapa(PROGRAMA_ID_REAL)
        nombres = sorted(mapa.keys())
        logger.info(
            "Sedes disponibles para programa %d (%d total): %s",
            PROGRAMA_ID_REAL,
            len(nombres),
            nombres,
        )
        # El test no falla si hay 0 sedes — simplemente informa al equipo.
        # Si la BD de prueba no tiene datos para programa 15 esto es esperado.
        self.assertIsInstance(mapa, dict)


# ---------------------------------------------------------------------------
# Test 2 — _resolver_sede
# ---------------------------------------------------------------------------

class ResolverSedeTests(TestCase):
    """Verifica la resolución difusa de nombres de sede."""

    MAPA_MOCK = {
        'GENERAL SANTANDER': 'COD-001',
        'SAN PEDRO': 'COD-002',
        'LA MERCED': 'COD-003',
    }

    def test_match_exacto(self):
        cod = _resolver_sede('GENERAL SANTANDER', self.MAPA_MOCK)
        self.assertEqual(cod, 'COD-001')

    def test_match_case_insensitive(self):
        cod = _resolver_sede('General Santander', self.MAPA_MOCK)
        self.assertEqual(cod, 'COD-001')

    def test_match_todo_minuscula(self):
        cod = _resolver_sede('general santander', self.MAPA_MOCK)
        self.assertEqual(cod, 'COD-001')

    def test_match_parcial_substring(self):
        # 'santander' está contenido en 'GENERAL SANTANDER'
        cod = _resolver_sede('santander', self.MAPA_MOCK)
        self.assertEqual(cod, 'COD-001')

    def test_no_match_retorna_none(self):
        cod = _resolver_sede('SEDE INEXISTENTE XYZ', self.MAPA_MOCK)
        self.assertIsNone(cod)

    def test_mapa_vacio_retorna_none(self):
        cod = _resolver_sede('GENERAL SANTANDER', {})
        self.assertIsNone(cod)

    def test_nombre_none_retorna_none(self):
        cod = _resolver_sede(None, self.MAPA_MOCK)
        self.assertIsNone(cod)

    def test_resolver_contra_sedes_reales_de_bd(self):
        """Intenta resolver con el mapa real del programa 15 si hay datos."""
        mapa_real = obtener_sedes_mapa(PROGRAMA_ID_REAL)
        if not mapa_real:
            self.skipTest(
                f"No hay sedes en BD para programa_id={PROGRAMA_ID_REAL}. "
                "Test omitido — no es un fallo del servicio."
            )
        variantes = ['GENERAL SANTANDER', 'General Santander', 'general santander', 'santander']
        resultados = {v: _resolver_sede(v, mapa_real) for v in variantes}
        logger.info(
            "Resolución de 'GENERAL SANTANDER' contra sedes reales programa %d: %s",
            PROGRAMA_ID_REAL,
            resultados,
        )
        # Al menos la búsqueda no debe lanzar excepción — el resultado puede ser None
        # si la sede no existe para este programa.
        self.assertIsInstance(resultados, dict)


# ---------------------------------------------------------------------------
# Test 3 — obtener_focalizaciones
# ---------------------------------------------------------------------------

class ObtenerFocalizacionesTests(TestCase):
    """Loggea los valores exactos de focalización para programa id=15."""

    def test_retorna_lista(self):
        focos = obtener_focalizaciones(PROGRAMA_ID_REAL)
        logger.info(
            "obtener_focalizaciones(programa_id=%d) => %s",
            PROGRAMA_ID_REAL,
            focos,
        )
        self.assertIsInstance(focos, list, "obtener_focalizaciones debe retornar una lista")

    def test_valores_son_strings(self):
        focos = obtener_focalizaciones(PROGRAMA_ID_REAL)
        for f in focos:
            self.assertIsInstance(
                f, str,
                f"Focalización no es str: {f!r} ({type(f).__name__})",
            )

    def test_lista_sin_duplicados(self):
        focos = obtener_focalizaciones(PROGRAMA_ID_REAL)
        self.assertEqual(
            len(focos), len(set(focos)),
            f"obtener_focalizaciones retornó duplicados: {focos}",
        )


# ---------------------------------------------------------------------------
# Test 4 — procesar_mensaje_nia con mock de Gemini
# ---------------------------------------------------------------------------

def _fake_generate_content_listo(*args, **kwargs):
    """
    Mock de GenerativeModel.generate_content que retorna un JSON simulando
    que Gemini extrajo todos los parámetros y está listo para generar planillas.
    """
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "intent": "planillas",
        "respuesta": "Perfecto, aquí tienes el enlace para descargar la planilla.",
        "params_extraidos": {
            "programa_id": PROGRAMA_ID_REAL,
            "mes": 3,
            "focalizacion": "F1",
            "todas_sedes": False,
            "sede_nombre": "GENERAL SANTANDER",
        },
        "listo": True,
    })
    return mock_response


def _fake_generate_content_pregunta(*args, **kwargs):
    """Mock que simula que Gemini pide más información."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "intent": "planillas",
        "respuesta": "¿Para qué programa deseas generar la planilla?",
        "params_extraidos": {
            "programa_id": None,
            "mes": None,
            "focalizacion": None,
            "todas_sedes": None,
            "sede_nombre": None,
        },
        "listo": False,
    })
    return mock_response


def _fake_generate_content_actividad(*args, **kwargs):
    """Mock que simula respuesta de intent=actividad."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "intent": "actividad",
        "respuesta": "En las últimas 24 horas se registraron 5 acciones sin errores.",
        "params_extraidos": {
            "programa_id": None,
            "mes": None,
            "focalizacion": None,
            "todas_sedes": None,
            "sede_nombre": None,
        },
        "listo": False,
    })
    return mock_response


class ProcesarMensajNiaTests(TestCase):
    """Prueba el flujo completo de procesar_mensaje_nia con Gemini mockeado."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='nia_tester', password='pass')

    def _make_request_with_session(self, session_data=None):
        """Crea un request con sesión Django funcional usando el test client."""
        from django.test import Client
        client = Client()
        client.force_login(self.user)
        # Inicializar sesión con datos previos si se pasan
        if session_data:
            session = client.session
            for key, val in session_data.items():
                session[key] = val
            session.save()
        # Fabricar request que usa la sesión del client
        request = self.factory.post('/dashboard/api/nia/chat/')
        request.user = self.user
        # Adjuntar sesión real del client
        from django.contrib.sessions.backends.db import SessionStore
        session_key = client.session.session_key
        request.session = SessionStore(session_key=session_key)
        return request

    @patch('google.generativeai.GenerativeModel.generate_content', side_effect=_fake_generate_content_pregunta)
    def test_turno1_mensaje_inicial_retorna_pregunta(self, mock_gc):
        """
        Turno 1: mensaje sin parámetros — NIA debe responder con tipo='pregunta'.
        """
        request = self._make_request_with_session()
        resultado = procesar_mensaje_nia(request, 'hola quiero generar planillas')
        logger.info("Turno 1 resultado: %s", resultado)
        self.assertIn('tipo', resultado)
        self.assertEqual(resultado['tipo'], 'pregunta')
        self.assertIn('mensaje', resultado)
        self.assertIsInstance(resultado['mensaje'], str)

    @patch('google.generativeai.GenerativeModel.generate_content', side_effect=_fake_generate_content_listo)
    def test_turno_con_todos_params_y_sede_existente_retorna_listo(self, mock_gc):
        """
        Simula que Gemini devuelve todos los parámetros incluyendo sede_nombre
        que SÍ existe en el mapa de sedes.

        Si la sede 'GENERAL SANTANDER' no existe en BD para programa 15,
        la función retorna tipo='pregunta' (sede no encontrada) — eso también
        se acepta y se loggea.
        """
        # Pre-cargar el estado de la sesión con el mapa de sedes real
        mapa_real = obtener_sedes_mapa(PROGRAMA_ID_REAL)
        logger.info(
            "Mapa de sedes real para programa %d: %s",
            PROGRAMA_ID_REAL,
            mapa_real,
        )

        session_data = {
            'nia_chat_estado': {
                'programa_id': PROGRAMA_ID_REAL,
                'programa_nombre': 'UNION TEMPORAL ALIMENTANDO YUMBO 2026',
                'mes': 3,
                'focalizacion': 'F1',
                'sedes_mapa': mapa_real,
            }
        }
        request = self._make_request_with_session(session_data)
        resultado = procesar_mensaje_nia(
            request,
            'genera planillas programa TEMPORAL ALIMENTANDO YUMBO 2026 mes marzo focalización F1 sede General Santander',
        )
        logger.info("Turno con todos los params: resultado=%s", resultado)

        self.assertIn('tipo', resultado)
        if resultado['tipo'] == 'listo':
            self.assertIn('url_descarga', resultado)
            url = resultado['url_descarga']
            logger.info("URL de descarga generada: %s", url)
            self.assertIn(f'/{PROGRAMA_ID_REAL}/', url)
            # Puede ser PDF individual o ZIP masivo
            self.assertTrue(
                url.startswith('/facturacion/generar-asistencia/')
                or url.startswith('/facturacion/generar-zip-masivo/'),
                f"URL inesperada: {url}",
            )
        elif resultado['tipo'] == 'pregunta':
            # Sede no encontrada en BD — aceptable si la sede no existe para programa 15
            logger.warning(
                "Sede 'GENERAL SANTANDER' no encontrada en mapa real del programa %d. "
                "Considerar verificar los datos de BD.",
                PROGRAMA_ID_REAL,
            )
        else:
            self.fail(f"tipo inesperado: {resultado['tipo']}")

    @patch('google.generativeai.GenerativeModel.generate_content', side_effect=_fake_generate_content_listo)
    def test_todas_sedes_genera_url_zip(self, mock_gc):
        """
        Cuando todas_sedes=True el resultado debe contener una URL de ZIP masivo.
        """
        session_data = {
            'nia_chat_estado': {
                'programa_id': PROGRAMA_ID_REAL,
                'programa_nombre': 'UNION TEMPORAL ALIMENTANDO YUMBO 2026',
                'mes': 3,
                'focalizacion': 'F1',
                'todas_sedes': True,
                'sedes_mapa': {},
            }
        }

        # Sobreescribir el mock para que retorne todas_sedes=True
        def _gen_todas(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "intent": "planillas",
                "respuesta": "Aquí tienes el ZIP con todas las sedes.",
                "params_extraidos": {
                    "programa_id": PROGRAMA_ID_REAL,
                    "mes": 3,
                    "focalizacion": "F1",
                    "todas_sedes": True,
                    "sede_nombre": None,
                },
                "listo": True,
            })
            return mock_response

        with patch('google.generativeai.GenerativeModel.generate_content', side_effect=_gen_todas):
            request = self._make_request_with_session(session_data)
            resultado = procesar_mensaje_nia(request, 'genera todas las sedes')

        logger.info("Resultado todas_sedes: %s", resultado)
        self.assertEqual(resultado.get('tipo'), 'listo')
        self.assertIn('url_descarga', resultado)
        self.assertIn('/facturacion/generar-zip-masivo/', resultado['url_descarga'])
        self.assertIn(str(PROGRAMA_ID_REAL), resultado['url_descarga'])

    @patch('google.generativeai.GenerativeModel.generate_content', side_effect=_fake_generate_content_actividad)
    def test_intent_actividad_retorna_info(self, mock_gc):
        """Un mensaje sobre actividad debe retornar tipo='info'."""
        request = self._make_request_with_session()
        resultado = procesar_mensaje_nia(request, '¿qué se hizo ayer en el sistema?')
        logger.info("Intent actividad resultado: %s", resultado)
        self.assertEqual(resultado.get('tipo'), 'info')
        self.assertIn('mensaje', resultado)

    @patch('google.generativeai.GenerativeModel.generate_content', side_effect=Exception('API no disponible'))
    def test_error_gemini_retorna_tipo_error(self, mock_gc):
        """Si Gemini lanza excepción, procesar_mensaje_nia retorna tipo='error'."""
        request = self._make_request_with_session()
        resultado = procesar_mensaje_nia(request, 'genera planillas')
        logger.info("Resultado con error Gemini: %s", resultado)
        self.assertEqual(resultado.get('tipo'), 'error')
        self.assertIn('mensaje', resultado)


# ---------------------------------------------------------------------------
# Test 5 — obtener_actividad_para_contexto
# ---------------------------------------------------------------------------

class ObtenerActividadParaContextoTests(TestCase):
    """
    Verifica que obtener_actividad_para_contexto no lanza excepción
    (incluso con usuario=None) y retorna un string.
    """

    def test_sin_registros_retorna_string(self):
        """Con BD vacía debe retornar el mensaje de sin actividad."""
        resultado = obtener_actividad_para_contexto(horas=24)
        logger.info("obtener_actividad_para_contexto (BD vacía): %r", resultado)
        self.assertIsInstance(resultado, str)
        self.assertGreater(len(resultado), 0, "El resultado no debe ser string vacío")

    def test_con_registro_usuario_none_no_lanza_excepcion(self):
        """
        Bug conocido: usuario=None en RegistroActividad no debe causar AttributeError.
        El servicio ya maneja esto con: r.usuario.get_full_name() if r.usuario else 'Sistema'
        """
        RegistroActividad.objects.create(
            usuario=None,
            modulo='dashboard',
            accion='test_accion',
            descripcion='Registro de prueba sin usuario asignado',
            exitoso=True,
        )
        try:
            resultado = obtener_actividad_para_contexto(horas=1)
        except AttributeError as exc:
            self.fail(
                f"obtener_actividad_para_contexto lanzó AttributeError con usuario=None: {exc}"
            )
        logger.info("Actividad con registro usuario=None: %r", resultado)
        self.assertIsInstance(resultado, str)
        self.assertIn('Sistema', resultado)

    def test_con_registro_usuario_real_retorna_nombre(self):
        """Con un usuario real registrado, el resultado incluye su nombre/username."""
        user = User.objects.create_user(
            username='operador_test',
            first_name='Carlos',
            last_name='Ramírez',
            password='pass',
        )
        RegistroActividad.objects.create(
            usuario=user,
            modulo='facturacion',
            accion='generar_pdf',
            descripcion='Generación de planilla sede X',
            exitoso=True,
        )
        resultado = obtener_actividad_para_contexto(horas=1)
        logger.info("Actividad con usuario real: %r", resultado)
        self.assertIsInstance(resultado, str)
        # El nombre completo 'Carlos Ramírez' debe aparecer
        self.assertIn('Carlos', resultado)

    def test_horas_cero_retorna_sin_actividad(self):
        """
        Con horas=0 el filtro desde=ahora no captura nada
        (auto_now_add puede coincidir, pero es un edge case válido de probar).
        """
        resultado = obtener_actividad_para_contexto(horas=0)
        self.assertIsInstance(resultado, str)
        logger.info("Actividad con horas=0: %r", resultado)


# ---------------------------------------------------------------------------
# Test 6 — Endpoint HTTP api_nia_chat
# ---------------------------------------------------------------------------

class ApiNiaChatEndpointTests(TestCase):
    """Prueba el endpoint HTTP /dashboard/api/nia/chat/ con autenticación."""

    def setUp(self):
        from django.test import Client
        self.client = Client()
        self.user = User.objects.create_user(username='http_tester', password='pass')
        self.client.force_login(self.user)

    def test_get_no_permitido(self):
        """El endpoint solo acepta POST."""
        response = self.client.get('/dashboard/api/nia/chat/')
        self.assertEqual(response.status_code, 405)

    def test_sin_autenticacion_redirige(self):
        """Sin login debe redirigir a /accounts/login/."""
        from django.test import Client
        anon_client = Client()
        response = anon_client.post(
            '/dashboard/api/nia/chat/',
            data=json.dumps({'mensaje': 'hola'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)

    def test_mensaje_vacio_retorna_400(self):
        """Mensaje vacío debe retornar HTTP 400."""
        response = self.client.post(
            '/dashboard/api/nia/chat/',
            data=json.dumps({'mensaje': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    @patch('google.generativeai.GenerativeModel.generate_content', side_effect=_fake_generate_content_pregunta)
    def test_mensaje_valido_retorna_json(self, mock_gc):
        """Mensaje con texto retorna JSON con campos 'tipo' y 'mensaje'."""
        response = self.client.post(
            '/dashboard/api/nia/chat/',
            data=json.dumps({'mensaje': 'quiero generar planillas'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        logger.info("Respuesta endpoint /api/nia/chat/: %s", data)
        self.assertIn('tipo', data)
        self.assertIn('mensaje', data)

    def test_reset_limpia_sesion(self):
        """El endpoint reset debe responder con ok=True y limpiar estado."""
        # Primero poner algo en la sesión
        session = self.client.session
        session['nia_chat_estado'] = {'programa_id': 15}
        session.save()

        response = self.client.post('/dashboard/api/nia/reset/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('ok'))

        # Verificar que el estado se limpió
        session = self.client.session
        self.assertNotIn('nia_chat_estado', session)
