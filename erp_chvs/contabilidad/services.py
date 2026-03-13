from django.db import models, transaction
from django.utils import timezone

from .models import (
    RegistroContable, Factura, ItemChecklist,
    VerificacionChecklist, HistorialEstado
)


class ContabilidadService:

    # ------------------------------------------------------------------ #
    # Método interno de transición de estado                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _transicion(registro, accion, estado_nuevo, fecha_field, comentario, usuario):
        """
        Aplica una transición de estado al registro:
        - Guarda el estado anterior
        - Actualiza estado y el campo de fecha correspondiente
        - Crea entrada en HistorialEstado
        - Persiste el registro
        """
        estado_anterior = registro.estado
        registro.estado = estado_nuevo
        if fecha_field:
            setattr(registro, fecha_field, timezone.now())
        registro.save()

        HistorialEstado.objects.create(
            registro=registro,
            accion=accion,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            comentario=comentario or '',
            usuario=usuario,
        )

    # ------------------------------------------------------------------ #
    # Crear registro                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    @transaction.atomic
    def crear_registro(lider, tipo, periodo_mes, periodo_ano, descripcion=''):
        """
        Crea un nuevo RegistroContable en estado BORRADOR y registra la creación
        en el historial.
        """
        registro = RegistroContable.objects.create(
            lider=lider,
            tipo=tipo,
            periodo_mes=periodo_mes,
            periodo_ano=periodo_ano,
            descripcion=descripcion,
            estado='BORRADOR',
        )
        HistorialEstado.objects.create(
            registro=registro,
            accion='CREACION',
            estado_anterior='',
            estado_nuevo='BORRADOR',
            comentario='Registro creado.',
            usuario=lider,
        )
        return registro

    # ------------------------------------------------------------------ #
    # Gestión de facturas                                                  #
    # ------------------------------------------------------------------ #

    ESTADOS_EDITABLES = ('BORRADOR', 'DEVUELTO_COMPRAS')

    @staticmethod
    def agregar_factura(registro, datos):
        """
        Agrega una Factura al registro. Solo permitido cuando el registro está
        en estado editable (BORRADOR o DEVUELTO_COMPRAS).
        """
        if registro.estado not in ContabilidadService.ESTADOS_EDITABLES:
            raise ValueError(
                f"No se puede agregar facturas en estado '{registro.estado}'. "
                f"Solo en: {', '.join(ContabilidadService.ESTADOS_EDITABLES)}"
            )
        factura = Factura.objects.create(
            registro=registro,
            numero_factura=datos.get('numero_factura', '').strip(),
            proveedor=datos.get('proveedor', '').strip(),
            concepto=datos.get('concepto', '').strip(),
            valor=datos['valor'],
            fecha_factura=datos['fecha_factura'],
        )
        return factura

    @staticmethod
    def eliminar_factura(factura, usuario):
        """
        Elimina una Factura. Solo permitido cuando el registro está en estado editable.
        """
        if factura.registro.estado not in ContabilidadService.ESTADOS_EDITABLES:
            raise ValueError(
                f"No se puede eliminar facturas en estado '{factura.registro.estado}'."
            )
        factura.delete()

    @staticmethod
    def editar_descripcion(registro, descripcion, usuario):
        """
        Edita la descripción del registro. Solo en estados editables.
        """
        if registro.estado not in ContabilidadService.ESTADOS_EDITABLES:
            raise ValueError(
                f"No se puede editar la descripción en estado '{registro.estado}'."
            )
        registro.descripcion = descripcion
        registro.save(update_fields=['descripcion'])

    # ------------------------------------------------------------------ #
    # Flujo de estados                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    @transaction.atomic
    def enviar(registro, usuario):
        """
        Transición BORRADOR/DEVUELTO → ENVIADO.
        Requiere al menos 1 factura. Distingue primer envío de reenvío.
        """
        if registro.estado not in ('BORRADOR', 'DEVUELTO_COMPRAS'):
            raise ValueError(
                f"Solo se puede enviar desde BORRADOR o DEVUELTO_COMPRAS. Estado actual: '{registro.estado}'"
            )
        if registro.facturas.count() == 0:
            raise ValueError("El registro debe tener al menos una factura antes de enviarse.")

        es_reenvio = registro.estado == 'DEVUELTO_COMPRAS'
        fecha_field = 'fecha_reenvio' if es_reenvio else 'fecha_envio'
        accion = 'REENVIO' if es_reenvio else 'ENVIO'

        ContabilidadService._transicion(
            registro=registro,
            accion=accion,
            estado_nuevo='ENVIADO',
            fecha_field=fecha_field,
            comentario='',
            usuario=usuario,
        )
        return registro

    @staticmethod
    @transaction.atomic
    def confirmar_recepcion(registro, usuario):
        """
        Transición ENVIADO → EN_REVISION_COMPRAS.
        Setea fecha de entrega física (primer envío) o reentrega (reenvío).
        Inicializa el checklist.
        """
        if registro.estado != 'ENVIADO':
            raise ValueError(
                f"Solo se puede confirmar recepción desde ENVIADO. Estado actual: '{registro.estado}'"
            )

        # Determinar si es primer envío o reenvío
        es_reenvio = registro.fecha_reenvio is not None
        fecha_entrega_field = 'fecha_reentrega_fisica' if es_reenvio else 'fecha_entrega_fisica'

        # Setear fecha de entrega y fecha de inicio de revisión
        now = timezone.now()
        setattr(registro, fecha_entrega_field, now)
        registro.fecha_inicio_revision_compras = now
        registro.estado = 'EN_REVISION_COMPRAS'
        registro.save()

        HistorialEstado.objects.create(
            registro=registro,
            accion='CONFIRMACION_REENTREGA' if es_reenvio else 'CONFIRMACION_RECEPCION',
            estado_anterior='ENVIADO',
            estado_nuevo='EN_REVISION_COMPRAS',
            comentario='',
            usuario=usuario,
        )

        ContabilidadService.inicializar_checklist(registro)
        return registro

    @staticmethod
    @transaction.atomic
    def devolver_compras(registro, usuario, comentario):
        """
        Transición EN_REVISION_COMPRAS → DEVUELTO_COMPRAS.
        Comentario obligatorio para justificar la devolución.
        """
        if registro.estado != 'EN_REVISION_COMPRAS':
            raise ValueError(
                f"Solo se puede devolver desde EN_REVISION_COMPRAS. Estado actual: '{registro.estado}'"
            )
        if not comentario or not comentario.strip():
            raise ValueError("El comentario es obligatorio para devolver el registro.")

        ContabilidadService._transicion(
            registro=registro,
            accion='DEVOLUCION_COMPRAS',
            estado_nuevo='DEVUELTO_COMPRAS',
            fecha_field='fecha_devolucion_compras',
            comentario=comentario,
            usuario=usuario,
        )
        return registro

    @staticmethod
    @transaction.atomic
    def aprobar_compras(registro, usuario, comentario=''):
        """
        Transición EN_REVISION_COMPRAS → APROBADO_COMPRAS.
        También acepta desde OBSERVADO_CONTABILIDAD (respuesta a observación).
        Valida que no haya ítems obligatorios en PENDIENTE.
        """
        if registro.estado not in ('EN_REVISION_COMPRAS', 'OBSERVADO_CONTABILIDAD'):
            raise ValueError(
                f"Solo se puede aprobar desde EN_REVISION_COMPRAS u OBSERVADO_CONTABILIDAD. "
                f"Estado actual: '{registro.estado}'"
            )

        # Validar checklist: no puede haber ítems obligatorios en PENDIENTE en ninguna factura
        pendientes_obligatorios = VerificacionChecklist.objects.filter(
            factura__registro=registro,
            estado='PENDIENTE',
            item__obligatorio=True,
        ).count()
        if pendientes_obligatorios > 0:
            raise ValueError(
                f"Hay {pendientes_obligatorios} ítem(s) obligatorio(s) del checklist sin verificar."
            )

        if registro.estado == 'OBSERVADO_CONTABILIDAD':
            # Respuesta a una observación de contabilidad
            ContabilidadService._transicion(
                registro=registro,
                accion='RESPUESTA_COMPRAS',
                estado_nuevo='APROBADO_COMPRAS',
                fecha_field='fecha_respuesta_compras',
                comentario=comentario,
                usuario=usuario,
            )
        else:
            ContabilidadService._transicion(
                registro=registro,
                accion='APROBACION_COMPRAS',
                estado_nuevo='APROBADO_COMPRAS',
                fecha_field='fecha_aprobacion_compras',
                comentario=comentario,
                usuario=usuario,
            )
        return registro

    @staticmethod
    def inicializar_checklist(registro):
        """
        Para cada factura del registro, crea filas de VerificacionChecklist
        con los ItemChecklist activos aplicables al tipo del registro.
        Usa ignore_conflicts=True para ser idempotente.
        """
        items = list(ItemChecklist.objects.filter(
            activo=True,
        ).filter(
            models.Q(tipo_proceso='AMBOS') | models.Q(tipo_proceso=registro.tipo)
        ))

        facturas = list(registro.facturas.all())
        verificaciones = [
            VerificacionChecklist(
                factura=factura,
                item=item,
                estado='PENDIENTE',
            )
            for factura in facturas
            for item in items
        ]
        VerificacionChecklist.objects.bulk_create(verificaciones, ignore_conflicts=True)

    @staticmethod
    @transaction.atomic
    def guardar_checklist(registro, items_data, usuario):
        """
        Actualiza el estado y observación de cada VerificacionChecklist.
        items_data: lista de dicts con {verificacion_id, estado, observacion}.
        Solo actualiza verificaciones que pertenezcan a facturas del registro.
        """
        now = timezone.now()
        ids_registro = set(registro.facturas.values_list('id', flat=True))
        for item_data in items_data:
            try:
                verificacion = VerificacionChecklist.objects.select_related('factura').get(
                    pk=item_data['verificacion_id'],
                )
                if verificacion.factura_id not in ids_registro:
                    continue
                verificacion.estado = item_data.get('estado', verificacion.estado)
                verificacion.observacion = item_data.get('observacion', '')
                verificacion.verificado_por = usuario
                verificacion.fecha_verificacion = now
                verificacion.save()
            except VerificacionChecklist.DoesNotExist:
                pass

    @staticmethod
    @transaction.atomic
    def observar_contabilidad(registro, usuario, comentario):
        """
        Transición APROBADO_COMPRAS → OBSERVADO_CONTABILIDAD.
        Comentario obligatorio. Setea fecha_inicio_revision_contabilidad y
        fecha_observacion_contabilidad.
        """
        if registro.estado != 'APROBADO_COMPRAS':
            raise ValueError(
                f"Solo se puede observar desde APROBADO_COMPRAS. Estado actual: '{registro.estado}'"
            )
        if not comentario or not comentario.strip():
            raise ValueError("El comentario es obligatorio para observar el registro.")

        now = timezone.now()
        registro.fecha_inicio_revision_contabilidad = now
        registro.fecha_observacion_contabilidad = now
        registro.estado = 'OBSERVADO_CONTABILIDAD'
        registro.save()

        HistorialEstado.objects.create(
            registro=registro,
            accion='OBSERVACION_CONTABILIDAD',
            estado_anterior='APROBADO_COMPRAS',
            estado_nuevo='OBSERVADO_CONTABILIDAD',
            comentario=comentario,
            usuario=usuario,
        )
        return registro

    @staticmethod
    @transaction.atomic
    def aprobar_contabilidad(registro, usuario, comentario=''):
        """
        Transición APROBADO_COMPRAS → CERRADO (aprobación + cierre en un solo paso).
        Setea fecha_inicio_revision_contabilidad, fecha_aprobacion_contabilidad y fecha_cierre.
        """
        if registro.estado != 'APROBADO_COMPRAS':
            raise ValueError(
                f"Solo se puede aprobar y cerrar desde APROBADO_COMPRAS. Estado actual: '{registro.estado}'"
            )

        now = timezone.now()
        registro.fecha_inicio_revision_contabilidad = now
        registro.fecha_aprobacion_contabilidad = now
        registro.fecha_cierre = now
        registro.estado = 'CERRADO'
        registro.save()

        HistorialEstado.objects.create(
            registro=registro,
            accion='APROBACION_CONTABILIDAD',
            estado_anterior='APROBADO_COMPRAS',
            estado_nuevo='APROBADO_CONTABILIDAD',
            comentario=comentario or '',
            usuario=usuario,
        )
        HistorialEstado.objects.create(
            registro=registro,
            accion='CIERRE',
            estado_anterior='APROBADO_CONTABILIDAD',
            estado_nuevo='CERRADO',
            comentario='Cierre automático tras aprobación de contabilidad.',
            usuario=usuario,
        )
        return registro

    @staticmethod
    @transaction.atomic
    def responder_observacion(registro, usuario, comentario):
        """
        Transición OBSERVADO_CONTABILIDAD → APROBADO_COMPRAS.
        Comentario obligatorio. Setea fecha_respuesta_compras.
        """
        if registro.estado != 'OBSERVADO_CONTABILIDAD':
            raise ValueError(
                f"Solo se puede responder desde OBSERVADO_CONTABILIDAD. Estado actual: '{registro.estado}'"
            )
        if not comentario or not comentario.strip():
            raise ValueError("El comentario es obligatorio para responder la observación.")

        ContabilidadService._transicion(
            registro=registro,
            accion='RESPUESTA_COMPRAS',
            estado_nuevo='APROBADO_COMPRAS',
            fecha_field='fecha_respuesta_compras',
            comentario=comentario,
            usuario=usuario,
        )
        return registro

    # ------------------------------------------------------------------ #
    # Bandejas                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_bandeja_compras():
        """
        Registros visibles para el área de Compras:
        - ENVIADO: para confirmar recepción de documentos físicos
        - EN_REVISION_COMPRAS: para hacer la revisión y checklist
        - OBSERVADO_CONTABILIDAD: para responder la observación de contabilidad
        """
        return RegistroContable.objects.filter(
            estado__in=('ENVIADO', 'EN_REVISION_COMPRAS', 'OBSERVADO_CONTABILIDAD')
        ).select_related('lider').order_by('-fecha_creacion')

    @staticmethod
    def get_bandeja_contabilidad():
        """
        Registros visibles para el área de Contabilidad:
        - APROBADO_COMPRAS: para segunda revisión y aprobación/observación
        """
        return RegistroContable.objects.filter(
            estado='APROBADO_COMPRAS'
        ).select_related('lider').order_by('-fecha_creacion')

    @staticmethod
    def get_dashboard_data(filtros=None):
        """
        Datos para el dashboard de gerencia:
        - Conteos por estado
        - Lista de registros con métricas de tiempo, agrupados por líder
        """
        from django.db.models import Count, Q
        from django.contrib.auth.models import User

        filtros = filtros or {}

        qs = RegistroContable.objects.select_related('lider').all()

        if filtros.get('lider_id'):
            qs = qs.filter(lider_id=filtros['lider_id'])
        if filtros.get('periodo_mes'):
            qs = qs.filter(periodo_mes=filtros['periodo_mes'])
        if filtros.get('periodo_ano'):
            qs = qs.filter(periodo_ano=filtros['periodo_ano'])
        if filtros.get('tipo'):
            qs = qs.filter(tipo=filtros['tipo'])
        if filtros.get('estado'):
            qs = qs.filter(estado=filtros['estado'])

        # Conteos por estado
        conteos = {}
        for estado_key, _ in RegistroContable.ESTADO_CHOICES:
            conteos[estado_key] = RegistroContable.objects.filter(estado=estado_key).count()

        # Lista de registros con métricas
        registros_data = []
        for r in qs.order_by('-fecha_creacion'):
            # Duración total en días (desde creación hasta cierre, o hasta ahora)
            fecha_fin = r.fecha_cierre or timezone.now()
            duracion_dias = (fecha_fin - r.fecha_creacion).days

            # Número de devoluciones
            num_devoluciones = r.historial.filter(accion='DEVOLUCION_COMPRAS').count()

            registros_data.append({
                'id': r.pk,
                'lider': r.lider.get_full_name() or r.lider.username,
                'lider_id': r.lider_id,
                'periodo_mes': r.periodo_mes,
                'periodo_ano': r.periodo_ano,
                'tipo': r.tipo,
                'tipo_display': r.get_tipo_display(),
                'estado': r.estado,
                'estado_display': r.get_estado_display(),
                'fecha_creacion': r.fecha_creacion.isoformat() if r.fecha_creacion else None,
                'fecha_envio': r.fecha_envio.isoformat() if r.fecha_envio else None,
                'fecha_cierre': r.fecha_cierre.isoformat() if r.fecha_cierre else None,
                'duracion_dias': duracion_dias,
                'num_devoluciones': num_devoluciones,
                'valor_total': float(r.valor_total),
                'total_documentos': r.total_documentos,
            })

        # Lista de líderes para filtros
        lideres = User.objects.filter(
            registros_contables__isnull=False
        ).distinct().values('id', 'username', 'first_name', 'last_name')

        return {
            'conteos': conteos,
            'registros': registros_data,
            'lideres': list(lideres),
        }


