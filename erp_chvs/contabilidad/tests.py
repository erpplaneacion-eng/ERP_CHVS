import json

from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.test import Client, TestCase

from .models import (
    Factura, HistorialEstado, ItemChecklist,
    RegistroContable, VerificacionChecklist,
)
from .services import ContabilidadService


class ContabilidadServiceTests(TestCase):

    def setUp(self):
        self.lider = User.objects.create_user(
            username='lider_test', password='test1234'
        )
        self.compras = User.objects.create_user(
            username='compras_test', password='test1234'
        )
        self.contabilidad = User.objects.create_user(
            username='contabilidad_test', password='test1234'
        )
        # La migración 0003 ya inserta los ítems de checklist reales.
        # Desactivamos todos para aislar las pruebas y creamos uno controlado.
        ItemChecklist.objects.all().update(activo=False)
        self.item = ItemChecklist.objects.create(
            nombre='Ítem test',
            tipo_proceso='AMBOS',
            obligatorio=True,
            activo=True,
            orden=1,
        )

    def _crear_registro_con_factura(self):
        registro = ContabilidadService.crear_registro(
            lider=self.lider,
            tipo='SERVICIOS',
            periodo_mes=3,
            periodo_ano=2025,
        )
        ContabilidadService.agregar_factura(registro, {
            'numero_factura': 'FV-001',
            'proveedor': 'Proveedor X',
            'concepto': 'Servicio de limpieza',
            'valor': 1000000,
            'fecha_factura': '2025-03-01',
        })
        return registro

    # ------------------------------------------------------------------ #
    # Creación y validaciones básicas                                      #
    # ------------------------------------------------------------------ #

    def test_crear_registro_borrador(self):
        registro = ContabilidadService.crear_registro(
            lider=self.lider, tipo='SERVICIOS', periodo_mes=1, periodo_ano=2025
        )
        self.assertEqual(registro.estado, 'BORRADOR')
        self.assertEqual(registro.lider, self.lider)
        historial = HistorialEstado.objects.filter(registro=registro, accion='CREACION')
        self.assertEqual(historial.count(), 1)

    def test_agregar_factura_en_borrador(self):
        registro = ContabilidadService.crear_registro(
            lider=self.lider, tipo='SERVICIOS', periodo_mes=1, periodo_ano=2025
        )
        ContabilidadService.agregar_factura(registro, {
            'numero_factura': 'FV-001',
            'proveedor': 'Proveedor',
            'concepto': 'Concepto',
            'valor': 500000,
            'fecha_factura': '2025-01-15',
        })
        self.assertEqual(registro.facturas.count(), 1)

    def test_no_puede_agregar_factura_en_estado_enviado(self):
        registro = self._crear_registro_con_factura()
        ContabilidadService.enviar(registro, self.lider)
        with self.assertRaises(ValueError):
            ContabilidadService.agregar_factura(registro, {
                'numero_factura': 'FV-002',
                'proveedor': 'X',
                'concepto': 'Y',
                'valor': 100,
                'fecha_factura': '2025-03-01',
            })

    def test_no_puede_enviar_sin_facturas(self):
        registro = ContabilidadService.crear_registro(
            lider=self.lider, tipo='SERVICIOS', periodo_mes=1, periodo_ano=2025
        )
        with self.assertRaises(ValueError):
            ContabilidadService.enviar(registro, self.lider)

    # ------------------------------------------------------------------ #
    # Flujo completo: BORRADOR → CERRADO                                   #
    # ------------------------------------------------------------------ #

    def test_flujo_aprobacion_completa(self):
        registro = self._crear_registro_con_factura()

        # Enviar
        ContabilidadService.enviar(registro, self.lider)
        self.assertEqual(registro.estado, 'ENVIADO')
        self.assertIsNotNone(registro.fecha_envio)

        # Confirmar recepción
        ContabilidadService.confirmar_recepcion(registro, self.compras)
        self.assertEqual(registro.estado, 'EN_REVISION_COMPRAS')
        self.assertIsNotNone(registro.fecha_entrega_fisica)
        # El checklist se inicializa: exactamente 1 verificación por factura
        # (solo el ítem activo creado en setUp; los de migración fueron desactivados)
        factura = registro.facturas.first()
        total_verificaciones = VerificacionChecklist.objects.filter(
            factura__registro=registro
        ).count()
        items_activos_para_tipo = ItemChecklist.objects.filter(
            activo=True
        ).filter(
            Q(tipo_proceso='AMBOS') | Q(tipo_proceso=registro.tipo)
        ).count()
        self.assertEqual(total_verificaciones, items_activos_para_tipo)

        # Aprobar factura (marcar todos los ítems obligatorios como OK)
        verificacion = VerificacionChecklist.objects.filter(
            factura=factura, item__obligatorio=True
        ).first()
        ContabilidadService.guardar_checklist(
            registro,
            [{'verificacion_id': verificacion.pk, 'estado': 'OK', 'observacion': ''}],
            self.compras,
        )
        ContabilidadService.aprobar_factura(factura, self.compras)
        factura.refresh_from_db()
        self.assertEqual(factura.estado_compras, 'APROBADA')

        # Finalizar revisión → APROBADO_COMPRAS
        ContabilidadService.finalizar_revision_compras(registro, self.compras)
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'APROBADO_COMPRAS')

        # Aprobar y cerrar por Contabilidad
        ContabilidadService.aprobar_contabilidad(registro, self.contabilidad, 'Todo correcto')
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'CERRADO')
        self.assertIsNotNone(registro.fecha_cierre)

    # ------------------------------------------------------------------ #
    # Flujo de devolución                                                  #
    # ------------------------------------------------------------------ #

    def test_flujo_devolucion_y_reenvio(self):
        registro = self._crear_registro_con_factura()
        ContabilidadService.enviar(registro, self.lider)
        ContabilidadService.confirmar_recepcion(registro, self.compras)

        # Devolver factura
        factura = registro.facturas.first()
        ContabilidadService.devolver_factura(factura, self.compras, 'Falta firma')
        factura.refresh_from_db()
        self.assertEqual(factura.estado_compras, 'DEVUELTA')

        # Finalizar revisión → DEVUELTO_COMPRAS
        ContabilidadService.finalizar_revision_compras(registro, self.compras)
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'DEVUELTO_COMPRAS')

        # Reenviar
        ContabilidadService.enviar(registro, self.lider)
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'ENVIADO')
        self.assertIsNotNone(registro.fecha_reenvio)
        # Las facturas DEVUELTA deben resetear a PENDIENTE
        factura.refresh_from_db()
        self.assertEqual(factura.estado_compras, 'PENDIENTE')

    def test_split_facturas_mixtas(self):
        """Cuando hay facturas aprobadas Y devueltas, finalizar debe hacer split."""
        registro = ContabilidadService.crear_registro(
            lider=self.lider, tipo='SERVICIOS', periodo_mes=3, periodo_ano=2025
        )
        # Agregar dos facturas
        ContabilidadService.agregar_factura(registro, {
            'numero_factura': 'FV-A', 'proveedor': 'P1', 'concepto': 'C1',
            'valor': 500000, 'fecha_factura': '2025-03-01',
        })
        ContabilidadService.agregar_factura(registro, {
            'numero_factura': 'FV-B', 'proveedor': 'P2', 'concepto': 'C2',
            'valor': 800000, 'fecha_factura': '2025-03-01',
        })

        ContabilidadService.enviar(registro, self.lider)
        ContabilidadService.confirmar_recepcion(registro, self.compras)

        facturas = list(registro.facturas.order_by('numero_factura'))
        fv_a, fv_b = facturas[0], facturas[1]

        # Aprobar FV-A (marcar checklist OK)
        ver_a = VerificacionChecklist.objects.filter(factura=fv_a, item__obligatorio=True).first()
        ContabilidadService.guardar_checklist(
            registro, [{'verificacion_id': ver_a.pk, 'estado': 'OK', 'observacion': ''}], self.compras
        )
        ContabilidadService.aprobar_factura(fv_a, self.compras)

        # Devolver FV-B
        ContabilidadService.devolver_factura(fv_b, self.compras, 'Falta firma')

        # Finalizar → debe hacer split
        registro_orig, nuevo = ContabilidadService.finalizar_revision_compras(registro, self.compras)

        # El original queda DEVUELTO con solo la factura devuelta
        registro_orig.refresh_from_db()
        self.assertEqual(registro_orig.estado, 'DEVUELTO_COMPRAS')
        self.assertEqual(registro_orig.facturas.count(), 1)
        self.assertEqual(registro_orig.facturas.first().numero_factura, 'FV-B')

        # El nuevo registro tiene la factura aprobada y va directo a APROBADO_COMPRAS
        self.assertIsNotNone(nuevo)
        nuevo.refresh_from_db()
        self.assertEqual(nuevo.estado, 'APROBADO_COMPRAS')
        self.assertEqual(nuevo.facturas.count(), 1)
        self.assertEqual(nuevo.facturas.first().numero_factura, 'FV-A')

        # Trazabilidad: el nuevo apunta al origen
        self.assertEqual(nuevo.registro_origen_id, registro_orig.pk)

        # El nuevo aparece en la bandeja de contabilidad de inmediato
        bandeja = ContabilidadService.get_bandeja_contabilidad()
        self.assertIn(nuevo, bandeja)
        self.assertNotIn(registro_orig, bandeja)

    def test_devolucion_requiere_comentario(self):
        registro = self._crear_registro_con_factura()
        ContabilidadService.enviar(registro, self.lider)
        ContabilidadService.confirmar_recepcion(registro, self.compras)
        factura = registro.facturas.first()
        with self.assertRaises(ValueError):
            ContabilidadService.devolver_factura(factura, self.compras, '')

    # ------------------------------------------------------------------ #
    # Observación de Contabilidad                                          #
    # ------------------------------------------------------------------ #

    def test_observacion_y_respuesta(self):
        registro = self._crear_registro_con_factura()
        ContabilidadService.enviar(registro, self.lider)
        ContabilidadService.confirmar_recepcion(registro, self.compras)
        # Aprobar factura: marcar el único ítem obligatorio activo como OK
        factura = registro.facturas.first()
        verificacion = VerificacionChecklist.objects.filter(
            factura=factura, item__obligatorio=True
        ).first()
        ContabilidadService.guardar_checklist(
            registro,
            [{'verificacion_id': verificacion.pk, 'estado': 'OK', 'observacion': ''}],
            self.compras,
        )
        ContabilidadService.aprobar_factura(factura, self.compras)
        ContabilidadService.finalizar_revision_compras(registro, self.compras)

        # Observar
        ContabilidadService.observar_contabilidad(registro, self.contabilidad, 'Falta soporte')
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'OBSERVADO_CONTABILIDAD')

        # Responder observación
        ContabilidadService.responder_observacion(registro, self.compras, 'Soporte adjuntado')
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'APROBADO_COMPRAS')

    def test_observacion_requiere_comentario(self):
        registro = self._crear_registro_con_factura()
        ContabilidadService.enviar(registro, self.lider)
        ContabilidadService.confirmar_recepcion(registro, self.compras)
        factura = registro.facturas.first()
        verificacion = VerificacionChecklist.objects.filter(
            factura=factura, item__obligatorio=True
        ).first()
        ContabilidadService.guardar_checklist(
            registro,
            [{'verificacion_id': verificacion.pk, 'estado': 'OK', 'observacion': ''}],
            self.compras,
        )
        ContabilidadService.aprobar_factura(factura, self.compras)
        ContabilidadService.finalizar_revision_compras(registro, self.compras)
        with self.assertRaises(ValueError):
            ContabilidadService.observar_contabilidad(registro, self.contabilidad, '')

    # ------------------------------------------------------------------ #
    # Propiedades del modelo                                               #
    # ------------------------------------------------------------------ #

    def test_valor_total_suma_facturas(self):
        registro = ContabilidadService.crear_registro(
            lider=self.lider, tipo='SERVICIOS', periodo_mes=1, periodo_ano=2025
        )
        ContabilidadService.agregar_factura(registro, {
            'numero_factura': 'F1', 'proveedor': 'A', 'concepto': 'C1',
            'valor': 300000, 'fecha_factura': '2025-01-01',
        })
        ContabilidadService.agregar_factura(registro, {
            'numero_factura': 'F2', 'proveedor': 'B', 'concepto': 'C2',
            'valor': 700000, 'fecha_factura': '2025-01-02',
        })
        self.assertEqual(registro.valor_total, 1000000)
        self.assertEqual(registro.total_documentos, 2)

    # ------------------------------------------------------------------ #
    # Dashboard data                                                       #
    # ------------------------------------------------------------------ #

    def test_dashboard_data_conteos(self):
        self._crear_registro_con_factura()  # BORRADOR
        data = ContabilidadService.get_dashboard_unificado()
        self.assertIn('kpis', data)
        self.assertIn('BORRADOR', data['kpis'])
        self.assertGreaterEqual(data['kpis']['BORRADOR'], 1)
        self.assertIn('lideres', data)

    # ------------------------------------------------------------------ #
    # Bandeja de Compras                                                   #
    # ------------------------------------------------------------------ #

    def test_bandeja_compras_solo_estados_relevantes(self):
        registro = self._crear_registro_con_factura()
        # BORRADOR no aparece en bandeja
        self.assertNotIn(registro, ContabilidadService.get_bandeja_compras())
        # ENVIADO sí aparece
        ContabilidadService.enviar(registro, self.lider)
        self.assertIn(registro, ContabilidadService.get_bandeja_compras())


# =========================================================================== #
# Tests: devolución parcial de Contabilidad (nuevos métodos)                  #
# =========================================================================== #

class ContabilidadDevolucionParcialServiceTests(TestCase):
    """
    Cubre los tres métodos nuevos del servicio:
      - aprobar_factura_contabilidad
      - devolver_factura_contabilidad
      - finalizar_revision_contabilidad
    y la modificación en responder_observacion que resetea estados.
    """

    def setUp(self):
        self.lider = User.objects.create_user(username='lider2', password='test1234')
        self.compras = User.objects.create_user(username='compras2', password='test1234')
        self.contabilidad_user = User.objects.create_user(username='contabilidad2', password='test1234')

        # Aislar ítems de checklist de la migración
        ItemChecklist.objects.all().update(activo=False)
        self.item = ItemChecklist.objects.create(
            nombre='Ítem test contabilidad',
            tipo_proceso='AMBOS',
            obligatorio=True,
            activo=True,
            orden=1,
        )

    # ------------------------------------------------------------------ #
    # Helpers internos                                                     #
    # ------------------------------------------------------------------ #

    def _llevar_a_aprobado_compras(self, num_facturas=1):
        """
        Crea un registro con N facturas y lo lleva hasta APROBADO_COMPRAS.
        Retorna (registro, lista_de_facturas).
        """
        registro = ContabilidadService.crear_registro(
            lider=self.lider,
            tipo='SERVICIOS',
            periodo_mes=4,
            periodo_ano=2025,
        )
        for i in range(num_facturas):
            ContabilidadService.agregar_factura(registro, {
                'numero_factura': f'FC-{i + 1:03d}',
                'proveedor': f'Proveedor {i + 1}',
                'concepto': 'Servicio test contabilidad',
                'valor': 1000000,
                'fecha_factura': '2025-04-01',
            })

        ContabilidadService.enviar(registro, self.lider)
        ContabilidadService.confirmar_recepcion(registro, self.compras)

        facturas = list(registro.facturas.order_by('numero_factura'))
        for factura in facturas:
            verificacion = VerificacionChecklist.objects.filter(
                factura=factura, item__obligatorio=True
            ).first()
            ContabilidadService.guardar_checklist(
                registro,
                [{'verificacion_id': verificacion.pk, 'estado': 'OK', 'observacion': ''}],
                self.compras,
            )
            ContabilidadService.aprobar_factura(factura, self.compras)

        ContabilidadService.finalizar_revision_compras(registro, self.compras)
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'APROBADO_COMPRAS')
        return registro, facturas

    # ------------------------------------------------------------------ #
    # aprobar_factura_contabilidad                                         #
    # ------------------------------------------------------------------ #

    def test_aprobar_factura_contabilidad_ok(self):
        registro, facturas = self._llevar_a_aprobado_compras()
        factura = facturas[0]

        ContabilidadService.aprobar_factura_contabilidad(factura, self.contabilidad_user)
        factura.refresh_from_db()

        self.assertEqual(factura.estado_contabilidad, 'APROBADA')
        self.assertEqual(factura.comentario_devolucion_contabilidad, '')

    def test_aprobar_factura_contabilidad_estado_incorrecto(self):
        """Registro en BORRADOR — debe lanzar ValueError."""
        registro = ContabilidadService.crear_registro(
            lider=self.lider, tipo='SERVICIOS', periodo_mes=4, periodo_ano=2025
        )
        ContabilidadService.agregar_factura(registro, {
            'numero_factura': 'FC-999',
            'proveedor': 'P',
            'concepto': 'C',
            'valor': 500000,
            'fecha_factura': '2025-04-01',
        })
        factura = registro.facturas.first()

        with self.assertRaises(ValueError):
            ContabilidadService.aprobar_factura_contabilidad(factura, self.contabilidad_user)

    def test_aprobar_factura_contabilidad_ya_decidida(self):
        """Factura ya aprobada por Contabilidad — no se puede decidir de nuevo."""
        registro, facturas = self._llevar_a_aprobado_compras()
        factura = facturas[0]
        ContabilidadService.aprobar_factura_contabilidad(factura, self.contabilidad_user)

        with self.assertRaises(ValueError):
            ContabilidadService.aprobar_factura_contabilidad(factura, self.contabilidad_user)

    # ------------------------------------------------------------------ #
    # devolver_factura_contabilidad                                        #
    # ------------------------------------------------------------------ #

    def test_devolver_factura_contabilidad_ok(self):
        registro, facturas = self._llevar_a_aprobado_compras()
        factura = facturas[0]

        ContabilidadService.devolver_factura_contabilidad(
            factura, self.contabilidad_user, 'Falta soporte contable'
        )
        factura.refresh_from_db()

        self.assertEqual(factura.estado_contabilidad, 'DEVUELTA')
        self.assertEqual(factura.comentario_devolucion_contabilidad, 'Falta soporte contable')

    def test_devolver_factura_contabilidad_sin_comentario(self):
        registro, facturas = self._llevar_a_aprobado_compras()
        factura = facturas[0]

        with self.assertRaises(ValueError):
            ContabilidadService.devolver_factura_contabilidad(
                factura, self.contabilidad_user, ''
            )

    # ------------------------------------------------------------------ #
    # finalizar_revision_contabilidad                                      #
    # ------------------------------------------------------------------ #

    def test_finalizar_revision_todas_aprobadas(self):
        """Todas las facturas aprobadas → estado CERRADO, retorna (registro, None)."""
        registro, facturas = self._llevar_a_aprobado_compras(num_facturas=2)
        for f in facturas:
            ContabilidadService.aprobar_factura_contabilidad(f, self.contabilidad_user)

        resultado, nuevo = ContabilidadService.finalizar_revision_contabilidad(
            registro, self.contabilidad_user
        )
        resultado.refresh_from_db()

        self.assertEqual(resultado.estado, 'CERRADO')
        self.assertIsNone(nuevo)
        self.assertIsNotNone(resultado.fecha_cierre)

    def test_finalizar_revision_todas_devueltas(self):
        """Todas devueltas → estado OBSERVADO_CONTABILIDAD, retorna (registro, None)."""
        registro, facturas = self._llevar_a_aprobado_compras(num_facturas=2)
        for f in facturas:
            ContabilidadService.devolver_factura_contabilidad(
                f, self.contabilidad_user, 'Documentación incompleta'
            )

        resultado, nuevo = ContabilidadService.finalizar_revision_contabilidad(
            registro, self.contabilidad_user
        )
        resultado.refresh_from_db()

        self.assertEqual(resultado.estado, 'OBSERVADO_CONTABILIDAD')
        self.assertIsNone(nuevo)

    def test_finalizar_revision_split(self):
        """
        Una aprobada + una devuelta → SPLIT.
        Nuevo registro queda CERRADO con la factura aprobada.
        Original queda OBSERVADO_CONTABILIDAD con la devuelta.
        """
        registro, facturas = self._llevar_a_aprobado_compras(num_facturas=2)
        fc_aprobada, fc_devuelta = facturas[0], facturas[1]

        ContabilidadService.aprobar_factura_contabilidad(fc_aprobada, self.contabilidad_user)
        ContabilidadService.devolver_factura_contabilidad(
            fc_devuelta, self.contabilidad_user, 'Falta firma del proveedor'
        )

        registro_orig, nuevo = ContabilidadService.finalizar_revision_contabilidad(
            registro, self.contabilidad_user
        )
        registro_orig.refresh_from_db()

        # Original: OBSERVADO_CONTABILIDAD con la factura devuelta
        self.assertEqual(registro_orig.estado, 'OBSERVADO_CONTABILIDAD')
        self.assertEqual(registro_orig.facturas.count(), 1)
        self.assertEqual(registro_orig.facturas.first().numero_factura, fc_devuelta.numero_factura)

        # Nuevo: CERRADO con la factura aprobada
        self.assertIsNotNone(nuevo)
        nuevo.refresh_from_db()
        self.assertEqual(nuevo.estado, 'CERRADO')
        self.assertEqual(nuevo.facturas.count(), 1)
        self.assertEqual(nuevo.facturas.first().numero_factura, fc_aprobada.numero_factura)

        # Trazabilidad de split
        self.assertEqual(nuevo.registro_origen_id, registro_orig.pk)

    def test_finalizar_revision_con_pendientes(self):
        """Hay facturas sin decidir → ValueError antes de poder finalizar."""
        registro, facturas = self._llevar_a_aprobado_compras(num_facturas=2)
        # Solo aprobamos una; la otra queda PENDIENTE
        ContabilidadService.aprobar_factura_contabilidad(facturas[0], self.contabilidad_user)

        with self.assertRaises(ValueError):
            ContabilidadService.finalizar_revision_contabilidad(
                registro, self.contabilidad_user
            )

    # ------------------------------------------------------------------ #
    # responder_observacion resetea estado_contabilidad                    #
    # ------------------------------------------------------------------ #

    def test_responder_observacion_resetea_estado_contabilidad(self):
        """
        Tras responder_observacion (OBSERVADO_CONTABILIDAD → APROBADO_COMPRAS),
        las facturas que estaban DEVUELTA deben quedar en PENDIENTE con comentario vacío.
        """
        registro, facturas = self._llevar_a_aprobado_compras(num_facturas=2)
        fc1, fc2 = facturas[0], facturas[1]

        # Contabilidad devuelve ambas → todas DEVUELTA
        ContabilidadService.devolver_factura_contabilidad(
            fc1, self.contabilidad_user, 'Error en fecha'
        )
        ContabilidadService.devolver_factura_contabilidad(
            fc2, self.contabilidad_user, 'Proveedor incorrecto'
        )

        # Finalizar → OBSERVADO_CONTABILIDAD (todas devueltas, sin split)
        ContabilidadService.finalizar_revision_contabilidad(registro, self.contabilidad_user)
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'OBSERVADO_CONTABILIDAD')

        # Compras responde la observación
        ContabilidadService.responder_observacion(
            registro, self.compras, 'Documentos corregidos y adjuntados'
        )
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'APROBADO_COMPRAS')

        # Las facturas deben tener estado_contabilidad=PENDIENTE y comentario vacío
        for f in [fc1, fc2]:
            f.refresh_from_db()
            self.assertEqual(f.estado_contabilidad, 'PENDIENTE')
            self.assertEqual(f.comentario_devolucion_contabilidad, '')


# =========================================================================== #
# Tests: endpoints API de devolución parcial Contabilidad                     #
# =========================================================================== #

class ContabilidadDevolucionParcialAPITests(TestCase):

    def setUp(self):
        self.client = Client()

        self.lider = User.objects.create_user(username='api_lider', password='test1234')
        self.compras_user = User.objects.create_user(username='api_compras', password='test1234')
        self.contabilidad_user = User.objects.create_user(username='api_contabilidad', password='test1234')
        self.otro_user = User.objects.create_user(username='api_otro', password='test1234')

        # Grupos de rol
        grupo_contabilidad, _ = Group.objects.get_or_create(name='CONTABILIDAD')
        grupo_compras, _ = Group.objects.get_or_create(name='COMPRAS_CONTABLE')
        self.contabilidad_user.groups.add(grupo_contabilidad)
        self.compras_user.groups.add(grupo_compras)

        # Aislar checklist
        ItemChecklist.objects.all().update(activo=False)
        self.item = ItemChecklist.objects.create(
            nombre='Ítem API test',
            tipo_proceso='AMBOS',
            obligatorio=True,
            activo=True,
            orden=1,
        )

    def _llevar_a_aprobado_compras(self, num_facturas=1):
        registro = ContabilidadService.crear_registro(
            lider=self.lider,
            tipo='SERVICIOS',
            periodo_mes=5,
            periodo_ano=2025,
        )
        for i in range(num_facturas):
            ContabilidadService.agregar_factura(registro, {
                'numero_factura': f'FP-{i + 1:03d}',
                'proveedor': 'Proveedor API',
                'concepto': 'Test API',
                'valor': 2000000,
                'fecha_factura': '2025-05-01',
            })

        ContabilidadService.enviar(registro, self.lider)
        ContabilidadService.confirmar_recepcion(registro, self.compras_user)

        facturas = list(registro.facturas.order_by('numero_factura'))
        for factura in facturas:
            verificacion = VerificacionChecklist.objects.filter(
                factura=factura, item__obligatorio=True
            ).first()
            ContabilidadService.guardar_checklist(
                registro,
                [{'verificacion_id': verificacion.pk, 'estado': 'OK', 'observacion': ''}],
                self.compras_user,
            )
            ContabilidadService.aprobar_factura(factura, self.compras_user)

        ContabilidadService.finalizar_revision_compras(registro, self.compras_user)
        registro.refresh_from_db()
        return registro, facturas

    # ------------------------------------------------------------------ #
    # POST /api/facturas/<pk>/aprobar-contabilidad/                        #
    # ------------------------------------------------------------------ #

    def test_api_aprobar_factura_contabilidad(self):
        registro, facturas = self._llevar_a_aprobado_compras()
        self.client.login(username='api_contabilidad', password='test1234')

        response = self.client.post(
            f'/contabilidad/api/facturas/{facturas[0].pk}/aprobar-contabilidad/',
            content_type='application/json',
            data=json.dumps({}),
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        facturas[0].refresh_from_db()
        self.assertEqual(facturas[0].estado_contabilidad, 'APROBADA')

    def test_api_aprobar_factura_contabilidad_sin_permiso(self):
        """Usuario sin grupo CONTABILIDAD debe recibir 403."""
        registro, facturas = self._llevar_a_aprobado_compras()
        self.client.login(username='api_otro', password='test1234')

        response = self.client.post(
            f'/contabilidad/api/facturas/{facturas[0].pk}/aprobar-contabilidad/',
            content_type='application/json',
            data=json.dumps({}),
        )

        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------ #
    # POST /api/facturas/<pk>/devolver-contabilidad/                       #
    # ------------------------------------------------------------------ #

    def test_api_devolver_factura_contabilidad(self):
        registro, facturas = self._llevar_a_aprobado_compras()
        self.client.login(username='api_contabilidad', password='test1234')

        response = self.client.post(
            f'/contabilidad/api/facturas/{facturas[0].pk}/devolver-contabilidad/',
            content_type='application/json',
            data=json.dumps({'comentario': 'Falta soporte de pago'}),
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        facturas[0].refresh_from_db()
        self.assertEqual(facturas[0].estado_contabilidad, 'DEVUELTA')
        self.assertEqual(facturas[0].comentario_devolucion_contabilidad, 'Falta soporte de pago')

    def test_api_devolver_factura_contabilidad_sin_comentario(self):
        """Comentario vacío debe retornar success=False con el error del servicio."""
        registro, facturas = self._llevar_a_aprobado_compras()
        self.client.login(username='api_contabilidad', password='test1234')

        response = self.client.post(
            f'/contabilidad/api/facturas/{facturas[0].pk}/devolver-contabilidad/',
            content_type='application/json',
            data=json.dumps({'comentario': ''}),
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    # ------------------------------------------------------------------ #
    # POST /api/registros/<pk>/finalizar-revision-contabilidad/            #
    # ------------------------------------------------------------------ #

    def test_api_finalizar_revision_contabilidad_todas_aprobadas(self):
        registro, facturas = self._llevar_a_aprobado_compras(num_facturas=2)
        # Aprobar todas las facturas por servicio
        for f in facturas:
            ContabilidadService.aprobar_factura_contabilidad(f, self.contabilidad_user)

        self.client.login(username='api_contabilidad', password='test1234')
        response = self.client.post(
            f'/contabilidad/api/registros/{registro.pk}/finalizar-revision-contabilidad/',
            content_type='application/json',
            data=json.dumps({}),
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['estado'], 'CERRADO')
        self.assertIsNone(data['nuevo_registro_id'])

    def test_api_finalizar_revision_contabilidad_split(self):
        """Una aprobada + una devuelta → split, nuevo_registro_id no nulo."""
        registro, facturas = self._llevar_a_aprobado_compras(num_facturas=2)
        ContabilidadService.aprobar_factura_contabilidad(facturas[0], self.contabilidad_user)
        ContabilidadService.devolver_factura_contabilidad(
            facturas[1], self.contabilidad_user, 'Error de concepto'
        )

        self.client.login(username='api_contabilidad', password='test1234')
        response = self.client.post(
            f'/contabilidad/api/registros/{registro.pk}/finalizar-revision-contabilidad/',
            content_type='application/json',
            data=json.dumps({}),
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['nuevo_registro_id'])
        self.assertGreater(data['nuevo_registro_id'], 0)

        # Verificar que el nuevo registro existe y está CERRADO
        nuevo = RegistroContable.objects.get(pk=data['nuevo_registro_id'])
        self.assertEqual(nuevo.estado, 'CERRADO')

        # Verificar que el original quedó OBSERVADO_CONTABILIDAD
        registro.refresh_from_db()
        self.assertEqual(registro.estado, 'OBSERVADO_CONTABILIDAD')

    def test_api_finalizar_sin_permiso(self):
        """Sin rol CONTABILIDAD → 403."""
        registro, facturas = self._llevar_a_aprobado_compras()
        ContabilidadService.aprobar_factura_contabilidad(facturas[0], self.contabilidad_user)

        self.client.login(username='api_otro', password='test1234')
        response = self.client.post(
            f'/contabilidad/api/registros/{registro.pk}/finalizar-revision-contabilidad/',
            content_type='application/json',
            data=json.dumps({}),
        )

        self.assertEqual(response.status_code, 403)

    def test_api_finalizar_sin_autenticar(self):
        """Sin sesión → redirige a login (302)."""
        registro, facturas = self._llevar_a_aprobado_compras()

        response = self.client.post(
            f'/contabilidad/api/registros/{registro.pk}/finalizar-revision-contabilidad/',
            content_type='application/json',
            data=json.dumps({}),
        )

        self.assertEqual(response.status_code, 302)
