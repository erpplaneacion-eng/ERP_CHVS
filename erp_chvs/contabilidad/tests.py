from django.contrib.auth.models import User
from django.db.models import Q
from django.test import TestCase

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
