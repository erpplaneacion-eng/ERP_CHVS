from datetime import timedelta

import pytz
from django.db import models, transaction
from django.utils import timezone

from django.contrib.auth.models import User

from .models import (
    RegistroContable, Factura, ItemChecklist,
    VerificacionChecklist, HistorialEstado
)

_COLOMBIA_TZ = pytz.timezone('America/Bogota')
_MAX_HORAS_LABORALES = 5
_HORA_INICIO = 7   # 7am
_HORA_FIN = 15     # 3pm


def horas_laborales_entre(inicio, fin):
    """
    Calcula horas laborales (lun-vie, 7am-4pm hora Colombia) entre dos datetimes aware.
    Retorna float. Devuelve 0.0 si inicio o fin son None o fin <= inicio.
    """
    if not inicio or not fin or fin <= inicio:
        return 0.0
    current = inicio.astimezone(_COLOMBIA_TZ)
    fin_col = fin.astimezone(_COLOMBIA_TZ)
    total = 0.0
    while current < fin_col:
        if current.weekday() >= 5:
            days_to_monday = 7 - current.weekday()
            current = (current + timedelta(days=days_to_monday)).replace(
                hour=_HORA_INICIO, minute=0, second=0, microsecond=0
            )
            continue
        inicio_hoy = current.replace(hour=_HORA_INICIO, minute=0, second=0, microsecond=0)
        fin_hoy = current.replace(hour=_HORA_FIN, minute=0, second=0, microsecond=0)
        if current < inicio_hoy:
            current = inicio_hoy
        if current >= fin_hoy:
            current = (current + timedelta(days=1)).replace(
                hour=_HORA_INICIO, minute=0, second=0, microsecond=0
            )
            continue
        fin_efectivo = min(fin_hoy, fin_col)
        total += (fin_efectivo - current).total_seconds() / 3600
        current = (current + timedelta(days=1)).replace(
            hour=_HORA_INICIO, minute=0, second=0, microsecond=0
        )
    return round(total, 2)


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
            fecha_recepcion_lider=datos.get('fecha_recepcion_lider') or None,
            observacion_retraso=datos.get('observacion_retraso', '').strip(),
            metodo_pago=datos.get('metodo_pago', '').strip(),
            tipo_contrato=datos.get('tipo_contrato', '').strip(),
        )
        return factura

    @staticmethod
    def cargar_facturas_desde_excel(registro, archivo):
        """
        Lee un Excel con 8 columnas (por posición) y crea facturas en bloque.
        Columnas esperadas: Nro Documento | Fecha | Estado Contable | Ref APPD |
                            Proveedor | Valor | Nro Orden Compra | Concepto
        Retorna (creadas: list[Factura], errores: list[dict]).
        """
        import re
        from decimal import Decimal, InvalidOperation
        import pandas as pd

        if registro.estado not in ContabilidadService.ESTADOS_EDITABLES:
            raise ValueError(
                f"No se puede cargar facturas en estado '{registro.estado}'. "
                f"Solo en: {', '.join(ContabilidadService.ESTADOS_EDITABLES)}"
            )
        if registro.tipo != 'MATERIAS_PRIMAS':
            raise ValueError("La carga por Excel solo aplica para registros de tipo MATERIAS_PRIMAS.")

        df = pd.read_excel(archivo, header=0, dtype=str)
        df = df.fillna('')

        if df.shape[1] < 8:
            raise ValueError(
                f"El archivo debe tener al menos 8 columnas. Se encontraron {df.shape[1]}."
            )

        tiene_col_recepcion = df.shape[1] >= 9

        creadas, errores = [], []

        for idx, row in df.iterrows():
            num_fila = idx + 2  # fila 1 = encabezado; datos desde fila 2
            try:
                numero_factura = str(row.iloc[0]).strip()
                if not numero_factura or numero_factura.lower() == 'nan':
                    errores.append({'fila': num_fila, 'error': 'Número de factura vacío'})
                    continue

                # Fecha — soporta texto "dd/mm/yyyy" o número serializado por pandas
                fecha_str = str(row.iloc[1]).strip()
                try:
                    fecha_factura = pd.to_datetime(fecha_str, dayfirst=True).date()
                except Exception:
                    errores.append({'fila': num_fila, 'error': f"Fecha inválida: '{fecha_str}'"})
                    continue

                estado_contable = str(row.iloc[2]).strip()
                referencia_appd = str(row.iloc[3]).strip()
                proveedor = str(row.iloc[4]).strip()
                if not proveedor or proveedor.lower() == 'nan':
                    errores.append({'fila': num_fila, 'error': 'Proveedor vacío'})
                    continue

                # Valor — soporta "$ 2.959.000,00" (colombiano) y "2959000.0" (numérico)
                valor_raw = str(row.iloc[5]).strip()
                valor_limpio = re.sub(r'[^\d.,]', '', valor_raw)
                if ',' in valor_limpio:
                    # Formato colombiano: puntos = miles, coma = decimal
                    valor_limpio = valor_limpio.replace('.', '').replace(',', '.')
                if not valor_limpio:
                    errores.append({'fila': num_fila, 'error': f"Valor inválido: '{valor_raw}'"})
                    continue
                valor = Decimal(valor_limpio)

                numero_orden_compra = str(row.iloc[6]).strip()
                observacion_raw = str(row.iloc[7]).strip()
                observacion_retraso = observacion_raw if observacion_raw and observacion_raw.lower() != 'nan' else ''
                concepto = f"Factura {numero_factura}"

                # Columna 8 (opcional): fecha de recepción por el líder
                fecha_recepcion_lider = None
                if tiene_col_recepcion:
                    recepcion_str = str(row.iloc[8]).strip()
                    if recepcion_str and recepcion_str.lower() not in ('nan', ''):
                        try:
                            fecha_recepcion_lider = pd.to_datetime(recepcion_str, dayfirst=True).date()
                        except Exception:
                            pass  # si no parsea, queda None sin bloquear la fila

                factura = Factura.objects.create(
                    registro=registro,
                    numero_factura=numero_factura,
                    fecha_factura=fecha_factura,
                    proveedor=proveedor,
                    concepto=concepto,
                    valor=valor,
                    observacion_retraso=observacion_retraso,
                    estado_contable=estado_contable,
                    referencia_appd=referencia_appd,
                    numero_orden_compra=numero_orden_compra,
                    fecha_recepcion_lider=fecha_recepcion_lider,
                )
                creadas.append(factura)

            except InvalidOperation:
                errores.append({'fila': num_fila, 'error': f"Valor no numérico: '{row.iloc[5]}'"})
            except Exception as e:
                errores.append({'fila': num_fila, 'error': str(e)})

        return creadas, errores

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
    def enviar(registro, usuario, justificacion=''):
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

        # Validar tiempo — timer del líder: fecha_creacion → ahora
        horas = horas_laborales_entre(registro.fecha_creacion, timezone.now())
        if horas > _MAX_HORAS_LABORALES and not justificacion:
            raise ValueError(
                f"Han transcurrido {horas:.1f} horas laborales desde la creación del registro "
                f"(máximo: {_MAX_HORAS_LABORALES}h). Debe ingresar una justificación de la demora."
            )
        if justificacion:
            registro.justificacion_demora_lider = justificacion.strip()
            registro.save(update_fields=['justificacion_demora_lider'])

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

        # MATERIAS_PRIMAS salta Compras completamente → APROBADO_COMPRAS directo
        if registro.tipo == 'MATERIAS_PRIMAS':
            now = timezone.now()
            registro.fecha_envio = now
            registro.fecha_aprobacion_compras = now
            registro.estado = 'APROBADO_COMPRAS'
            registro.save()
            HistorialEstado.objects.create(
                registro=registro,
                accion='ENVIO',
                estado_anterior='BORRADOR',
                estado_nuevo='APROBADO_COMPRAS',
                comentario='Registro de Materias Primas enviado directamente a Contabilidad (sin revisión de Compras).',
                usuario=usuario,
            )
            return registro

        # SERVICIOS: flujo normal con Compras
        comentario_envio = (
            "Registro reenviado a Compras tras corrección de facturas devueltas."
            if es_reenvio else
            "Registro enviado a Compras para revisión física de documentos."
        )
        ContabilidadService._transicion(
            registro=registro,
            accion=accion,
            estado_nuevo='ENVIADO',
            fecha_field=fecha_field,
            comentario=comentario_envio,
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

        comentario_recepcion = (
            "Compras confirmó la reentrega física de los documentos. Inicio de revisión (ciclo de corrección)."
            if es_reenvio else
            "Compras confirmó la recepción física de los documentos. Inicio de revisión de facturas y checklist."
        )
        HistorialEstado.objects.create(
            registro=registro,
            accion='CONFIRMACION_REENTREGA' if es_reenvio else 'CONFIRMACION_RECEPCION',
            estado_anterior='ENVIADO',
            estado_nuevo='EN_REVISION_COMPRAS',
            comentario=comentario_recepcion,
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
    def finalizar_revision_compras(registro, usuario, justificacion=''):
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

        # Validar tiempo — timer de Compras: fecha_entrega_fisica (o reentrega) → ahora
        fecha_inicio_compras = registro.fecha_reentrega_fisica or registro.fecha_entrega_fisica
        horas = horas_laborales_entre(fecha_inicio_compras, timezone.now())
        if horas > _MAX_HORAS_LABORALES and not justificacion:
            raise ValueError(
                f"Han transcurrido {horas:.1f} horas laborales desde la recepción del documento "
                f"(máximo: {_MAX_HORAS_LABORALES}h). Debe ingresar una justificación de la demora."
            )
        if justificacion:
            registro.justificacion_demora_compras = justificacion.strip()
            registro.save(update_fields=['justificacion_demora_compras'])

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
                comentario=(
                    f"Compras aprobó las {len(aprobadas)} factura(s). "
                    "Registro enviado a revisión de Contabilidad."
                ),
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
                comentario=(
                    f"Compras devolvió las {len(devueltas)} factura(s). "
                    "Registro regresa al líder para corrección desde la etapa de Revisión de Compras."
                ),
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
                f"Split de facturas desde Revisión de Compras: "
                f"{len(devueltas)} factura(s) devuelta(s) al líder para corrección — "
                f"{len(aprobadas)} factura(s) aprobada(s) trasladadas al registro RC-{nuevo.pk} para continuar en Contabilidad."
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
        Para MATERIAS_PRIMAS, los ítems de formato devolución solo se asignan
        a facturas que tengan tiene_formato_devolucion=True.
        """
        # Ítems base: solo los del tipo exacto del registro.
        # SERVICIOS → ítems SERVICIOS | MATERIAS_PRIMAS → ítems MATERIAS_PRIMAS
        items_base = list(ItemChecklist.objects.filter(
            activo=True,
            es_formato_devolucion=False,
            tipo_proceso=registro.tipo,
        ))

        # Ítems condicionales de formato devolución (solo para MATERIAS_PRIMAS)
        items_devolucion = list(ItemChecklist.objects.filter(
            activo=True,
            es_formato_devolucion=True,
            tipo_proceso=registro.tipo,
        ))

        # Solo facturas que están siendo revisadas en esta ronda
        facturas = list(registro.facturas.filter(estado_compras='PENDIENTE'))
        verificaciones = []
        for factura in facturas:
            items_aplicables = items_base + (
                items_devolucion if factura.tiene_formato_devolucion else []
            )
            for item in items_aplicables:
                verificaciones.append(VerificacionChecklist(
                    factura=factura,
                    item=item,
                    estado='PENDIENTE',
                ))
        VerificacionChecklist.objects.bulk_create(verificaciones, ignore_conflicts=True)

    @staticmethod
    @transaction.atomic
    def toggle_formato_devolucion(factura, usuario):
        """
        Activa/desactiva el flag tiene_formato_devolucion en una factura.
        Si se activa, inicializa los ítems de formato devolución para esa factura.
        Si se desactiva, elimina las verificaciones de ítems de formato devolución.
        Solo válido cuando el registro está en APROBADO_COMPRAS y la factura está PENDIENTE.
        """
        if factura.registro.estado != 'APROBADO_COMPRAS':
            raise ValueError("Solo se puede modificar facturas en estado APROBADO_COMPRAS.")
        if factura.estado_contabilidad != 'PENDIENTE':
            raise ValueError("Esta factura ya fue decidida.")

        factura.tiene_formato_devolucion = not factura.tiene_formato_devolucion
        factura.save(update_fields=['tiene_formato_devolucion'])

        if factura.tiene_formato_devolucion:
            items_dev = list(ItemChecklist.objects.filter(
                activo=True,
                es_formato_devolucion=True,
                tipo_proceso=factura.registro.tipo,
            ))
            verificaciones = [
                VerificacionChecklist(factura=factura, item=item, estado='PENDIENTE')
                for item in items_dev
            ]
            VerificacionChecklist.objects.bulk_create(verificaciones, ignore_conflicts=True)
        else:
            VerificacionChecklist.objects.filter(
                factura=factura,
                item__es_formato_devolucion=True,
            ).delete()

        return factura

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
    def aprobar_factura_contabilidad(factura, usuario):
        """
        Contabilidad aprueba una factura individual.
        Solo permitido cuando el registro está en APROBADO_COMPRAS.
        Para MATERIAS_PRIMAS, valida que el checklist obligatorio esté completo.
        """
        if factura.registro.estado != 'APROBADO_COMPRAS':
            raise ValueError("Solo se puede aprobar facturas en estado APROBADO_COMPRAS.")
        if factura.estado_contabilidad != 'PENDIENTE':
            raise ValueError("Esta factura ya fue decidida por Contabilidad.")
        if factura.registro.tipo == 'MATERIAS_PRIMAS':
            pendientes = VerificacionChecklist.objects.filter(
                factura=factura,
                estado='PENDIENTE',
                item__obligatorio=True,
                item__tipo_proceso='MATERIAS_PRIMAS',
            ).count()
            if pendientes > 0:
                raise ValueError(
                    f"Hay {pendientes} ítem(s) obligatorio(s) del checklist sin verificar en esta factura."
                )
        factura.estado_contabilidad = 'APROBADA'
        factura.comentario_devolucion_contabilidad = ''
        factura.save(update_fields=['estado_contabilidad', 'comentario_devolucion_contabilidad'])

    @staticmethod
    @transaction.atomic
    def devolver_factura_contabilidad(factura, usuario, comentario):
        """
        Contabilidad devuelve una factura individual a Compras con un motivo.
        Solo permitido cuando el registro está en APROBADO_COMPRAS.
        """
        if factura.registro.estado != 'APROBADO_COMPRAS':
            raise ValueError("Solo se puede devolver facturas en estado APROBADO_COMPRAS.")
        if factura.estado_contabilidad != 'PENDIENTE':
            raise ValueError("Esta factura ya fue decidida por Contabilidad.")
        if not comentario or not comentario.strip():
            raise ValueError("El motivo de devolución es obligatorio.")
        factura.estado_contabilidad = 'DEVUELTA'
        factura.comentario_devolucion_contabilidad = comentario.strip()
        factura.save(update_fields=['estado_contabilidad', 'comentario_devolucion_contabilidad'])

    @staticmethod
    @transaction.atomic
    def finalizar_revision_contabilidad(registro, usuario, justificacion=''):
        """
        Finaliza la revisión de Contabilidad cuando todas las facturas han sido decididas.
        - Todas APROBADA → CERRADO (aprobación y cierre directos)
        - Todas DEVUELTA → OBSERVADO_CONTABILIDAD (sin split, vuelve a Compras)
        - Mixtas           → SPLIT:
            · Nuevo registro con APROBADAS → CERRADO
            · Registro original con DEVUELTAS → OBSERVADO_CONTABILIDAD (Compras corrige)
        - No puede haber facturas en PENDIENTE.
        Retorna (registro_original, registro_nuevo_o_None).
        """
        if registro.estado != 'APROBADO_COMPRAS':
            raise ValueError(
                f"Solo se puede finalizar desde APROBADO_COMPRAS. Estado actual: '{registro.estado}'"
            )
        facturas = list(registro.facturas.all())
        if not facturas:
            raise ValueError("El registro no tiene facturas.")

        # Validar tiempo — timer de Contabilidad.
        # Si hubo ciclo de observación, el timer arranca desde fecha_respuesta_compras
        # (excluye el tiempo que el área respondiente tardó en responder).
        fecha_inicio_conta = registro.fecha_respuesta_compras or registro.fecha_aprobacion_compras
        horas = horas_laborales_entre(fecha_inicio_conta, timezone.now())
        if horas > _MAX_HORAS_LABORALES and not justificacion:
            raise ValueError(
                f"Han transcurrido {horas:.1f} horas laborales desde la aprobación de Compras "
                f"(máximo: {_MAX_HORAS_LABORALES}h). Debe ingresar una justificación de la demora."
            )
        if justificacion:
            registro.justificacion_demora_contabilidad = justificacion.strip()
            registro.save(update_fields=['justificacion_demora_contabilidad'])

        pendientes = [f for f in facturas if f.estado_contabilidad == 'PENDIENTE']
        if pendientes:
            raise ValueError(
                f"Hay {len(pendientes)} factura(s) sin decidir. "
                "Aprueba o devuelve cada factura antes de finalizar."
            )

        devueltas = [f for f in facturas if f.estado_contabilidad == 'DEVUELTA']
        aprobadas = [f for f in facturas if f.estado_contabilidad == 'APROBADA']

        now = timezone.now()

        if not devueltas:
            # Todas aprobadas — cerrar directamente
            registro.fecha_inicio_revision_contabilidad = registro.fecha_inicio_revision_contabilidad or now
            registro.fecha_aprobacion_contabilidad = now
            registro.fecha_cierre = now
            registro.estado = 'CERRADO'
            registro.save()
            HistorialEstado.objects.create(
                registro=registro,
                accion='APROBACION_CONTABILIDAD',
                estado_anterior='APROBADO_COMPRAS',
                estado_nuevo='APROBADO_CONTABILIDAD',
                comentario=f"Contabilidad aprobó las {len(aprobadas)} factura(s).",
                usuario=usuario,
            )
            HistorialEstado.objects.create(
                registro=registro,
                accion='CIERRE',
                estado_anterior='APROBADO_CONTABILIDAD',
                estado_nuevo='CERRADO',
                comentario='Registro cerrado definitivamente. Proceso contable completado.',
                usuario=usuario,
            )
            return registro, None

        if not aprobadas:
            # Todas devueltas — sin split, observar completo
            registro.fecha_inicio_revision_contabilidad = registro.fecha_inicio_revision_contabilidad or now
            registro.fecha_observacion_contabilidad = now
            registro.estado = 'OBSERVADO_CONTABILIDAD'
            registro.save()
            detalle_devueltas = '\n'.join(
                f"• {f.numero_factura} ({f.proveedor}): {f.comentario_devolucion_contabilidad or 'Sin motivo especificado'}"
                for f in devueltas
            )
            HistorialEstado.objects.create(
                registro=registro,
                accion='DEVOLUCION_CONTABILIDAD',
                estado_anterior='APROBADO_COMPRAS',
                estado_nuevo='OBSERVADO_CONTABILIDAD',
                comentario=(
                    f"Contabilidad devolvió {len(devueltas)} factura(s):\n{detalle_devueltas}"
                ),
                usuario=usuario,
            )
            return registro, None

        # --- SPLIT: hay aprobadas Y devueltas ---

        # 1. Crear nuevo registro para las facturas aprobadas → CERRADO
        nuevo = RegistroContable.objects.create(
            lider=registro.lider,
            tipo=registro.tipo,
            periodo_mes=registro.periodo_mes,
            periodo_ano=registro.periodo_ano,
            descripcion=registro.descripcion,
            estado='CERRADO',
            registro_origen=registro,
            fecha_envio=registro.fecha_envio,
            fecha_entrega_fisica=registro.fecha_entrega_fisica,
            fecha_inicio_revision_compras=registro.fecha_inicio_revision_compras,
            fecha_aprobacion_compras=registro.fecha_aprobacion_compras,
            fecha_inicio_revision_contabilidad=registro.fecha_inicio_revision_contabilidad or now,
            fecha_aprobacion_contabilidad=now,
            fecha_cierre=now,
        )
        HistorialEstado.objects.create(
            registro=nuevo,
            accion='CREACION',
            estado_anterior='',
            estado_nuevo='CERRADO',
            comentario=(
                f"Registro derivado de RC-{registro.pk} por split de Contabilidad. "
                f"{len(aprobadas)} factura(s) aprobada(s) cerradas."
            ),
            usuario=usuario,
        )
        HistorialEstado.objects.create(
            registro=nuevo,
            accion='CIERRE',
            estado_anterior='APROBADO_CONTABILIDAD',
            estado_nuevo='CERRADO',
            comentario='Registro cerrado definitivamente. Proceso contable completado.',
            usuario=usuario,
        )

        # 2. Mover facturas aprobadas al nuevo registro
        Factura.objects.filter(pk__in=[f.pk for f in aprobadas]).update(registro=nuevo)

        # 3. Registro original: queda con las devueltas → OBSERVADO_CONTABILIDAD
        registro.fecha_inicio_revision_contabilidad = registro.fecha_inicio_revision_contabilidad or now
        registro.fecha_observacion_contabilidad = now
        registro.estado = 'OBSERVADO_CONTABILIDAD'
        registro.save()
        detalle_devueltas_split = '\n'.join(
            f"• {f.numero_factura} ({f.proveedor}): {f.comentario_devolucion_contabilidad or 'Sin motivo especificado'}"
            for f in devueltas
        )
        HistorialEstado.objects.create(
            registro=registro,
            accion='DEVOLUCION_CONTABILIDAD',
            estado_anterior='APROBADO_COMPRAS',
            estado_nuevo='OBSERVADO_CONTABILIDAD',
            comentario=(
                f"Split: {len(aprobadas)} factura(s) aprobada(s) trasladadas al RC-{nuevo.pk}. "
                f"Facturas devueltas ({len(devueltas)}):\n{detalle_devueltas_split}"
            ),
            usuario=usuario,
        )
        return registro, nuevo

    @staticmethod
    @transaction.atomic
    def observar_contabilidad(registro, usuario, comentario, justificacion=''):
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

        # Validar tiempo — timer de Contabilidad.
        # Si hubo ciclo de observación, el timer arranca desde fecha_respuesta_compras.
        fecha_inicio_conta = registro.fecha_respuesta_compras or registro.fecha_aprobacion_compras
        horas = horas_laborales_entre(fecha_inicio_conta, timezone.now())
        if horas > _MAX_HORAS_LABORALES and not justificacion:
            raise ValueError(
                f"Han transcurrido {horas:.1f} horas laborales desde la aprobación de Compras "
                f"(máximo: {_MAX_HORAS_LABORALES}h). Debe ingresar una justificación de la demora."
            )
        if justificacion:
            registro.justificacion_demora_contabilidad = justificacion.strip()

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
    def aprobar_contabilidad(registro, usuario, comentario='', justificacion=''):
        """
        Transición APROBADO_COMPRAS → CERRADO (aprobación + cierre en un solo paso).
        Setea fecha_inicio_revision_contabilidad, fecha_aprobacion_contabilidad y fecha_cierre.
        """
        if registro.estado != 'APROBADO_COMPRAS':
            raise ValueError(
                f"Solo se puede aprobar y cerrar desde APROBADO_COMPRAS. Estado actual: '{registro.estado}'"
            )

        # Validar tiempo — timer de Contabilidad.
        # Si hubo ciclo de observación, el timer arranca desde fecha_respuesta_compras.
        fecha_inicio_conta = registro.fecha_respuesta_compras or registro.fecha_aprobacion_compras
        horas = horas_laborales_entre(fecha_inicio_conta, timezone.now())
        if horas > _MAX_HORAS_LABORALES and not justificacion:
            raise ValueError(
                f"Han transcurrido {horas:.1f} horas laborales desde la aprobación de Compras "
                f"(máximo: {_MAX_HORAS_LABORALES}h). Debe ingresar una justificación de la demora."
            )
        if justificacion:
            registro.justificacion_demora_contabilidad = justificacion.strip()

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
            comentario=comentario or 'Contabilidad aprobó el registro tras revisión de facturas y checklist.',
            usuario=usuario,
        )
        HistorialEstado.objects.create(
            registro=registro,
            accion='CIERRE',
            estado_anterior='APROBADO_CONTABILIDAD',
            estado_nuevo='CERRADO',
            comentario='Registro cerrado definitivamente. Proceso contable completado en todas las etapas.',
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

        # Resetear estado_contabilidad de facturas devueltas para que Contabilidad
        # pueda revisar nuevamente cuando el registro vuelva a APROBADO_COMPRAS.
        registro.facturas.filter(estado_contabilidad='DEVUELTA').update(
            estado_contabilidad='PENDIENTE',
            comentario_devolucion_contabilidad='',
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

    # ------------------------------------------------------------------ #
    # Bandejas                                                             #
    # ------------------------------------------------------------------ #

    ESTADOS_ACTIVOS_COMPRAS = ('ENVIADO', 'EN_REVISION_COMPRAS', 'OBSERVADO_CONTABILIDAD')
    ESTADOS_ACTIVOS_CONTABILIDAD = ('APROBADO_COMPRAS',)

    @staticmethod
    def get_bandeja_compras(solo_activos=True):
        """
        Registros visibles para el área de Compras.
        solo_activos=True  → solo los que requieren acción inmediata.
        solo_activos=False → historial completo (todo lo que ha pasado por Compras).
        """
        if solo_activos:
            estados = ContabilidadService.ESTADOS_ACTIVOS_COMPRAS
        else:
            estados = (
                'ENVIADO', 'EN_REVISION_COMPRAS', 'DEVUELTO_COMPRAS',
                'APROBADO_COMPRAS', 'OBSERVADO_CONTABILIDAD',
                'APROBADO_CONTABILIDAD', 'CERRADO',
            )
        # MATERIAS_PRIMAS nunca pasa por Compras — excluir siempre
        return RegistroContable.objects.filter(
            estado__in=estados
        ).exclude(
            tipo='MATERIAS_PRIMAS'
        ).select_related('lider').order_by('-fecha_creacion')

    @staticmethod
    def get_bandeja_contabilidad(solo_activos=True):
        """
        Registros visibles para el área de Contabilidad.
        solo_activos=True  → solo APROBADO_COMPRAS (pendientes de revisión).
        solo_activos=False → historial completo (todo lo que ha pasado por Contabilidad).
        """
        if solo_activos:
            estados = ContabilidadService.ESTADOS_ACTIVOS_CONTABILIDAD
        else:
            estados = (
                'APROBADO_COMPRAS', 'OBSERVADO_CONTABILIDAD',
                'APROBADO_CONTABILIDAD', 'CERRADO',
            )
        return RegistroContable.objects.filter(
            estado__in=estados
        ).select_related('lider').order_by('-fecha_creacion')

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
            revision_compras_list = []
            dias_retraso_carga_list = []
            total_devoluciones = 0

            for r in registros:
                fecha_estado = r.ultima_transicion or r.fecha_creacion
                dias_en_estado = (now - fecha_estado).days if fecha_estado else 0

                total_devoluciones += r.num_devoluciones

                # Horas laborales totales del proceso (fecha_creacion → fecha_cierre)
                dias_cierre = None
                if r.fecha_cierre and r.fecha_creacion:
                    dias_cierre = round(horas_laborales_entre(r.fecha_creacion, r.fecha_cierre), 1)
                    dias_cierre_list.append(dias_cierre)

                # Horas laborales que tardó el líder en corregir tras devolución
                dias_reentrega = None
                if r.fecha_reenvio and r.fecha_devolucion_compras:
                    dias_reentrega = round(horas_laborales_entre(r.fecha_devolucion_compras, r.fecha_reenvio), 1)
                    dias_reentrega_list.append(dias_reentrega)

                # Retraso de carga: fecha_recepcion_lider − fecha_factura (máximo entre facturas del registro)
                max_retraso_carga = None
                retrasos = []
                for fac in r.facturas.all():
                    if fac.fecha_factura and fac.fecha_recepcion_lider:
                        retraso = max(0, (fac.fecha_recepcion_lider - fac.fecha_factura).days)
                        retrasos.append(retraso)
                if retrasos:
                    max_retraso_carga = max(retrasos)
                    dias_retraso_carga_list.append(max_retraso_carga)

                # T. Revisión Compras: desde recepción física hasta decisión (aprobar o devolver)
                tiempo_revision_compras_h = None
                if r.fecha_entrega_fisica:
                    if r.fecha_devolucion_compras and r.fecha_reentrega_fisica:
                        # Con devolución: T1 + T2 de revisión interna
                        t1_rev = horas_laborales_entre(r.fecha_entrega_fisica, r.fecha_devolucion_compras)
                        t2_rev = horas_laborales_entre(r.fecha_reentrega_fisica, r.fecha_aprobacion_compras) if r.fecha_aprobacion_compras else 0
                        tiempo_revision_compras_h = round(t1_rev + t2_rev, 1)
                    elif r.fecha_devolucion_compras:
                        tiempo_revision_compras_h = round(horas_laborales_entre(r.fecha_entrega_fisica, r.fecha_devolucion_compras), 1)
                    elif r.fecha_aprobacion_compras:
                        tiempo_revision_compras_h = round(horas_laborales_entre(r.fecha_entrega_fisica, r.fecha_aprobacion_compras), 1)
                if tiempo_revision_compras_h is not None:
                    revision_compras_list.append(tiempo_revision_compras_h)

                # Tiempo por etapa en horas laborales (lun-vie, 7am-3pm Colombia)
                tiempo_lider_h = None
                tiempo_lider_t1_h = None
                tiempo_lider_t2_h = None
                if r.fecha_envio and r.fecha_creacion:
                    tiempo_lider_t1_h = round(horas_laborales_entre(r.fecha_creacion, r.fecha_envio), 1)
                    if r.fecha_reenvio and r.fecha_devolucion_compras:
                        # SERVICIOS: T2 = tiempo que el líder tardó en corregir tras devolución de Compras
                        tiempo_lider_t2_h = round(horas_laborales_entre(r.fecha_devolucion_compras, r.fecha_reenvio), 1)
                        tiempo_lider_h = round(tiempo_lider_t1_h + tiempo_lider_t2_h, 1)
                    elif r.tipo == 'MATERIAS_PRIMAS' and r.fecha_observacion_contabilidad and r.fecha_respuesta_compras:
                        # MATERIAS_PRIMAS: T2 = tiempo que el líder tardó en responder observación de Contabilidad
                        tiempo_lider_t2_h = round(horas_laborales_entre(r.fecha_observacion_contabilidad, r.fecha_respuesta_compras), 1)
                        tiempo_lider_h = round(tiempo_lider_t1_h + tiempo_lider_t2_h, 1)
                    else:
                        tiempo_lider_h = tiempo_lider_t1_h

                tiempo_compras_h = None
                tiempo_compras_t1_h = None
                tiempo_compras_t2_h = None
                tiempo_compras_t3_h = None
                # MATERIAS_PRIMAS nunca pasa por Compras → tiempo siempre None
                if r.tipo == 'SERVICIOS' and r.fecha_aprobacion_compras and r.fecha_envio:
                    if r.fecha_devolucion_compras and r.fecha_reenvio:
                        # Con devolución: T1 = envío líder → devolución, T2 = reenvío → aprobación
                        tiempo_compras_t1_h = round(horas_laborales_entre(r.fecha_envio, r.fecha_devolucion_compras), 1)
                        tiempo_compras_t2_h = round(horas_laborales_entre(r.fecha_reenvio, r.fecha_aprobacion_compras), 1)
                        tiempo_compras_h = round(tiempo_compras_t1_h + tiempo_compras_t2_h, 1)
                    else:
                        # Sin devolución: desde que el líder envió hasta que Compras aprobó
                        tiempo_compras_h = round(horas_laborales_entre(r.fecha_envio, r.fecha_aprobacion_compras), 1)
                    # T3: tiempo que Compras tardó en responder observación de Contabilidad
                    if r.fecha_observacion_contabilidad and r.fecha_respuesta_compras:
                        tiempo_compras_t3_h = round(horas_laborales_entre(r.fecha_observacion_contabilidad, r.fecha_respuesta_compras), 1)
                        tiempo_compras_h = round((tiempo_compras_h or 0) + tiempo_compras_t3_h, 1)

                tiempo_contabilidad_h = None
                tiempo_conta_t1_h = None
                tiempo_conta_t2_h = None
                if r.fecha_cierre and r.fecha_aprobacion_compras:
                    if r.fecha_observacion_contabilidad and r.fecha_respuesta_compras:
                        tiempo_conta_t1_h = round(horas_laborales_entre(r.fecha_aprobacion_compras, r.fecha_observacion_contabilidad), 1)
                        tiempo_conta_t2_h = round(horas_laborales_entre(r.fecha_respuesta_compras, r.fecha_cierre), 1)
                        tiempo_contabilidad_h = round(tiempo_conta_t1_h + tiempo_conta_t2_h, 1)
                    else:
                        tiempo_contabilidad_h = round(horas_laborales_entre(r.fecha_aprobacion_compras, r.fecha_cierre), 1)

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
                    'tiempo_revision_compras_h': tiempo_revision_compras_h,
                    'max_retraso_carga': max_retraso_carga,
                    'tiempo_lider_h': tiempo_lider_h,
                    'tiempo_lider_t1_h': tiempo_lider_t1_h,
                    'tiempo_lider_t2_h': tiempo_lider_t2_h,
                    'tiempo_compras_h': tiempo_compras_h,
                    'tiempo_compras_t1_h': tiempo_compras_t1_h,
                    'tiempo_compras_t2_h': tiempo_compras_t2_h,
                    'tiempo_compras_t3_h': tiempo_compras_t3_h,
                    'tiempo_contabilidad_h': tiempo_contabilidad_h,
                    'tiempo_conta_t1_h': tiempo_conta_t1_h,
                    'tiempo_conta_t2_h': tiempo_conta_t2_h,
                    'tuvo_observacion_contabilidad': bool(r.fecha_observacion_contabilidad and r.fecha_respuesta_compras),
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
            promedio_revision_compras = (
                round(sum(revision_compras_list) / len(revision_compras_list), 1)
                if revision_compras_list else None
            )
            max_revision_compras = max(revision_compras_list) if revision_compras_list else None
            promedio_retraso_carga = (
                round(sum(dias_retraso_carga_list) / len(dias_retraso_carga_list), 1)
                if dias_retraso_carga_list else None
            )
            max_retraso_carga_lider = max(dias_retraso_carga_list) if dias_retraso_carga_list else None
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
                'promedio_revision_compras': promedio_revision_compras,
                'max_revision_compras': max_revision_compras,
                'promedio_retraso_carga': promedio_retraso_carga,
                'max_retraso_carga': max_retraso_carga_lider,
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



