from django.db import models, transaction
from django.utils import timezone

from django.contrib.auth.models import User

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
        Elimina una Factura. En DEVUELTO_COMPRAS solo se pueden eliminar facturas DEVUELTA.
        """
        estado_registro = factura.registro.estado
        if estado_registro not in ContabilidadService.ESTADOS_EDITABLES:
            raise ValueError(
                f"No se puede eliminar facturas en estado '{estado_registro}'."
            )
        if estado_registro == 'DEVUELTO_COMPRAS' and factura.estado_compras != 'DEVUELTA':
            raise ValueError(
                "Solo se pueden eliminar facturas que fueron devueltas por Compras."
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

        if es_reenvio:
            # Resetear solo las facturas DEVUELTA; las APROBADA permanecen
            devueltas_ids = list(
                registro.facturas.filter(estado_compras='DEVUELTA').values_list('id', flat=True)
            )
            # Borrar su checklist anterior (se recreará en confirmar_recepcion)
            VerificacionChecklist.objects.filter(factura_id__in=devueltas_ids).delete()
            registro.facturas.filter(id__in=devueltas_ids).update(
                estado_compras='PENDIENTE', comentario_devolucion=''
            )

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
    def aprobar_factura(factura, usuario):
        """
        Compras aprueba una factura individual.
        Valida que no queden ítems obligatorios en PENDIENTE en esa factura.
        """
        if factura.registro.estado != 'EN_REVISION_COMPRAS':
            raise ValueError("Solo se puede aprobar facturas en estado EN_REVISION_COMPRAS.")
        if factura.estado_compras != 'PENDIENTE':
            raise ValueError("Esta factura ya fue decidida.")
        pendientes = VerificacionChecklist.objects.filter(
            factura=factura, estado='PENDIENTE', item__obligatorio=True,
        ).count()
        if pendientes > 0:
            raise ValueError(
                f"Hay {pendientes} ítem(s) obligatorio(s) del checklist sin verificar en esta factura."
            )
        factura.estado_compras = 'APROBADA'
        factura.comentario_devolucion = ''
        factura.save(update_fields=['estado_compras', 'comentario_devolucion'])

    @staticmethod
    @transaction.atomic
    def devolver_factura(factura, usuario, comentario):
        """
        Compras devuelve una factura individual al líder con un motivo.
        """
        if factura.registro.estado != 'EN_REVISION_COMPRAS':
            raise ValueError("Solo se puede devolver facturas en estado EN_REVISION_COMPRAS.")
        if factura.estado_compras != 'PENDIENTE':
            raise ValueError("Esta factura ya fue decidida.")
        if not comentario or not comentario.strip():
            raise ValueError("El motivo de devolución es obligatorio.")
        factura.estado_compras = 'DEVUELTA'
        factura.comentario_devolucion = comentario.strip()
        factura.save(update_fields=['estado_compras', 'comentario_devolucion'])

    @staticmethod
    @transaction.atomic
    def finalizar_revision_compras(registro, usuario):
        """
        Finaliza la revisión de Compras cuando todas las facturas han sido decididas.
        - Todas APROBADA          → APROBADO_COMPRAS (flujo normal)
        - Todas DEVUELTA          → DEVUELTO_COMPRAS (sin split)
        - Mixtas (ambas)          → SPLIT:
            · Nuevo registro con las APROBADAS → APROBADO_COMPRAS (va al contador ya)
            · Registro original con las DEVUELTAS → DEVUELTO_COMPRAS (líder corrige)
        - No puede haber facturas en PENDIENTE.
        Retorna (registro_original, registro_nuevo_o_None).
        """
        if registro.estado != 'EN_REVISION_COMPRAS':
            raise ValueError(
                f"Solo se puede finalizar desde EN_REVISION_COMPRAS. Estado actual: '{registro.estado}'"
            )
        facturas = list(registro.facturas.all())
        if not facturas:
            raise ValueError("El registro no tiene facturas.")

        pendientes = [f for f in facturas if f.estado_compras == 'PENDIENTE']
        if pendientes:
            raise ValueError(
                f"Hay {len(pendientes)} factura(s) sin decidir. "
                "Aprueba o devuelve cada factura antes de finalizar."
            )

        devueltas = [f for f in facturas if f.estado_compras == 'DEVUELTA']
        aprobadas = [f for f in facturas if f.estado_compras == 'APROBADA']

        if not devueltas:
            # Todas aprobadas — flujo normal
            ContabilidadService._transicion(
                registro=registro,
                accion='APROBACION_COMPRAS',
                estado_nuevo='APROBADO_COMPRAS',
                fecha_field='fecha_aprobacion_compras',
                comentario='',
                usuario=usuario,
            )
            return registro, None

        if not aprobadas:
            # Todas devueltas — sin split, devolver completo
            ContabilidadService._transicion(
                registro=registro,
                accion='DEVOLUCION_COMPRAS',
                estado_nuevo='DEVUELTO_COMPRAS',
                fecha_field='fecha_devolucion_compras',
                comentario=f"{len(devueltas)} factura(s) devuelta(s) al líder para corrección.",
                usuario=usuario,
            )
            return registro, None

        # --- SPLIT: hay aprobadas Y devueltas ---
        now = timezone.now()

        # 1. Crear nuevo registro para las facturas aprobadas
        nuevo = RegistroContable.objects.create(
            lider=registro.lider,
            tipo=registro.tipo,
            periodo_mes=registro.periodo_mes,
            periodo_ano=registro.periodo_ano,
            descripcion=registro.descripcion,
            estado='APROBADO_COMPRAS',
            registro_origen=registro,
            # Heredar fechas relevantes para mantener trazabilidad del tiempo
            fecha_envio=registro.fecha_envio,
            fecha_entrega_fisica=registro.fecha_entrega_fisica,
            fecha_inicio_revision_compras=registro.fecha_inicio_revision_compras,
            fecha_aprobacion_compras=now,
        )

        # Historial del nuevo registro
        HistorialEstado.objects.create(
            registro=nuevo,
            accion='CREACION',
            estado_anterior='',
            estado_nuevo='APROBADO_COMPRAS',
            comentario=(
                f"Registro derivado de RC-{registro.pk} por split de facturas. "
                f"{len(aprobadas)} factura(s) aprobada(s) trasladadas."
            ),
            usuario=usuario,
        )

        # 2. Mover facturas aprobadas al nuevo registro
        aprobadas_ids = [f.pk for f in aprobadas]
        Factura.objects.filter(pk__in=aprobadas_ids).update(registro=nuevo)

        # 3. Registro original: queda solo con las devueltas → DEVUELTO_COMPRAS
        ContabilidadService._transicion(
            registro=registro,
            accion='DEVOLUCION_COMPRAS',
            estado_nuevo='DEVUELTO_COMPRAS',
            fecha_field='fecha_devolucion_compras',
            comentario=(
                f"{len(devueltas)} factura(s) devuelta(s) al líder para corrección. "
                f"{len(aprobadas)} factura(s) aprobada(s) trasladadas al registro RC-{nuevo.pk}."
            ),
            usuario=usuario,
        )

        return registro, nuevo

    @staticmethod
    @transaction.atomic
    def aprobar_compras(registro, usuario, comentario=''):
        """
        Usado solo para la transición OBSERVADO_CONTABILIDAD → APROBADO_COMPRAS
        (respuesta de Compras a una observación de Contabilidad).
        """
        if registro.estado != 'OBSERVADO_CONTABILIDAD':
            raise ValueError(
                f"aprobar_compras solo acepta desde OBSERVADO_CONTABILIDAD. "
                f"Estado actual: '{registro.estado}'"
            )
        ContabilidadService._transicion(
            registro=registro,
            accion='RESPUESTA_COMPRAS',
            estado_nuevo='APROBADO_COMPRAS',
            fecha_field='fecha_respuesta_compras',
            comentario=comentario,
            usuario=usuario,
        )
        return registro

    @staticmethod
    def inicializar_checklist(registro):
        """
        Para cada factura PENDIENTE del registro, crea filas de VerificacionChecklist.
        Las facturas APROBADA mantienen su checklist anterior intacto.
        Usa ignore_conflicts=True para ser idempotente.
        """
        items = list(ItemChecklist.objects.filter(
            activo=True,
        ).filter(
            models.Q(tipo_proceso='AMBOS') | models.Q(tipo_proceso=registro.tipo)
        ))

        # Solo facturas que están siendo revisadas en esta ronda
        facturas = list(registro.facturas.filter(estado_compras='PENDIENTE'))
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
    @staticmethod
    def get_dashboard_unificado(filtros=None):
        """
        Vista unificada: KPIs globales + métricas históricas por líder.

        Por líder devuelve:
        - total_registros, total_activos, total_cerrados
        - total_devoluciones (eventos DEVOLUCION_COMPRAS acumulados)
        - valor_total_cerrado
        - promedio_dias_cierre / max_dias_cierre  (fecha_envio → fecha_cierre)
        - promedio_dias_reentrega / max_dias_reentrega  (fecha_devolucion → fecha_reenvio)
        - estado_critico (estado más urgente entre los registros activos)
        - registros: lista detallada con días_cierre y dias_reentrega por registro
        """
        from django.db.models import Count, Q, Subquery, OuterRef

        filtros = filtros or {}

        # KPIs globales (sin filtros de período/tipo para que siempre muestren totales reales)
        conteos = {
            estado_key: RegistroContable.objects.filter(estado=estado_key).count()
            for estado_key, _ in RegistroContable.ESTADO_CHOICES
        }

        # Base filtrada con anotaciones para evitar N+1
        qs_base = RegistroContable.objects.select_related(
            'lider', 'registro_origen'
        ).annotate(
            num_devoluciones=Count(
                'historial',
                filter=Q(historial__accion='DEVOLUCION_COMPRAS')
            ),
            ultima_transicion=Subquery(
                HistorialEstado.objects.filter(
                    registro=OuterRef('pk')
                ).order_by('-fecha').values('fecha')[:1]
            ),
        )

        if filtros.get('lider_id'):
            qs_base = qs_base.filter(lider_id=filtros['lider_id'])
        if filtros.get('periodo_mes'):
            qs_base = qs_base.filter(periodo_mes=filtros['periodo_mes'])
        if filtros.get('periodo_ano'):
            qs_base = qs_base.filter(periodo_ano=filtros['periodo_ano'])
        if filtros.get('tipo'):
            qs_base = qs_base.filter(tipo=filtros['tipo'])

        now = timezone.now()
        _prioridad = {
            'DEVUELTO_COMPRAS': 1,
            'OBSERVADO_CONTABILIDAD': 2,
            'ENVIADO': 3,
            'EN_REVISION_COMPRAS': 4,
            'APROBADO_COMPRAS': 5,
            'APROBADO_CONTABILIDAD': 6,
            'BORRADOR': 7,
        }

        lideres_ids = qs_base.values_list('lider_id', flat=True).distinct()
        lideres_qs = User.objects.filter(pk__in=lideres_ids).order_by(
            'first_name', 'last_name', 'username'
        )

        resultado = []
        for lider in lideres_qs:
            registros = list(qs_base.filter(lider=lider).order_by('-fecha_creacion'))

            registros_data = []
            dias_cierre_list = []
            dias_reentrega_list = []
            total_devoluciones = 0

            for r in registros:
                fecha_estado = r.ultima_transicion or r.fecha_creacion
                dias_en_estado = (now - fecha_estado).days if fecha_estado else 0

                total_devoluciones += r.num_devoluciones

                dias_cierre = None
                if r.fecha_cierre and r.fecha_envio:
                    dias_cierre = max(0, (r.fecha_cierre - r.fecha_envio).days)
                    dias_cierre_list.append(dias_cierre)

                dias_reentrega = None
                if r.fecha_reenvio and r.fecha_devolucion_compras:
                    dias_reentrega = max(0, (r.fecha_reenvio - r.fecha_devolucion_compras).days)
                    dias_reentrega_list.append(dias_reentrega)

                registros_data.append({
                    'id': r.pk,
                    'tipo': r.tipo,
                    'tipo_display': r.get_tipo_display(),
                    'periodo_mes': r.periodo_mes,
                    'periodo_ano': r.periodo_ano,
                    'estado': r.estado,
                    'estado_display': r.get_estado_display(),
                    'dias_en_estado': dias_en_estado,
                    'num_devoluciones': r.num_devoluciones,
                    'valor_total': float(r.valor_total),
                    'total_documentos': r.total_documentos,
                    'fecha_envio': r.fecha_envio.isoformat() if r.fecha_envio else None,
                    'fecha_cierre': r.fecha_cierre.isoformat() if r.fecha_cierre else None,
                    'dias_cierre': dias_cierre,
                    'dias_reentrega': dias_reentrega,
                    'registro_origen_id': r.registro_origen_id,
                    'es_derivado': r.registro_origen_id is not None,
                })

            activos = [x for x in registros_data if x['estado'] != 'CERRADO']
            cerrados = [x for x in registros_data if x['estado'] == 'CERRADO']

            promedio_dias_cierre = (
                round(sum(dias_cierre_list) / len(dias_cierre_list), 1)
                if dias_cierre_list else None
            )
            max_dias_cierre = max(dias_cierre_list) if dias_cierre_list else None
            promedio_dias_reentrega = (
                round(sum(dias_reentrega_list) / len(dias_reentrega_list), 1)
                if dias_reentrega_list else None
            )
            max_dias_reentrega = max(dias_reentrega_list) if dias_reentrega_list else None
            valor_total_cerrado = sum(x['valor_total'] for x in cerrados)

            estado_critico = min(
                (x['estado'] for x in activos),
                key=lambda e: _prioridad.get(e, 99),
                default=None,
            )

            resultado.append({
                'lider_id': lider.pk,
                'lider_nombre': lider.get_full_name() or lider.username,
                'lider_username': lider.username,
                'total_registros': len(registros_data),
                'total_activos': len(activos),
                'total_cerrados': len(cerrados),
                'total_devoluciones': total_devoluciones,
                'valor_total_cerrado': valor_total_cerrado,
                'promedio_dias_cierre': promedio_dias_cierre,
                'max_dias_cierre': max_dias_cierre,
                'promedio_dias_reentrega': promedio_dias_reentrega,
                'max_dias_reentrega': max_dias_reentrega,
                'estado_critico': estado_critico,
                'registros': registros_data,
            })

        resultado.sort(key=lambda x: (
            0 if x['total_activos'] > 0 else 1,
            _prioridad.get(x['estado_critico'] or '', 99),
        ))

        return {
            'kpis': conteos,
            'lideres': resultado,
        }



