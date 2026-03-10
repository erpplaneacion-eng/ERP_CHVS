from django.db import transaction
from django.utils import timezone

from nutricion.models import TablaMenus, TablaPreparaciones, TablaPreparacionIngredientes
from principal.models import RegistroActividad

from ..models import GeneracionIA, BorradorPreparacionIA, BorradorIngredienteIA


def importar_borrador(generacion_id: int, menu_id: int, request) -> dict:
    generacion = GeneracionIA.objects.select_related('id_modalidad').get(id=generacion_id)

    if generacion.estado != GeneracionIA.ESTADO_PENDIENTE:
        return {'ok': False, 'error': 'Solo se pueden importar borradores en estado pendiente_revision.'}

    try:
        menu = TablaMenus.objects.select_related('id_modalidad').get(id_menu=menu_id)
    except TablaMenus.DoesNotExist:
        return {'ok': False, 'error': f'Menú {menu_id} no encontrado.'}

    if str(menu.id_modalidad_id) != str(generacion.id_modalidad_id):
        return {'ok': False, 'error': 'El menú seleccionado no pertenece a la modalidad del borrador.'}

    preparaciones_borrador = BorradorPreparacionIA.objects.filter(
        generacion=generacion
    ).prefetch_related('ingredientes__alimento_icbf', 'componente_sugerido')

    creadas = 0
    advertencias = []

    try:
        with transaction.atomic():
            for prep_borrador in preparaciones_borrador:
                if prep_borrador.estado_validacion == BorradorPreparacionIA.INVALIDA:
                    advertencias.append(
                        f"'{prep_borrador.nombre_preparacion}' omitida: marcada como inválida."
                    )
                    continue

                ingredientes_validos = prep_borrador.ingredientes.filter(
                    estado_validacion=BorradorIngredienteIA.VALIDO,
                    alimento_icbf__isnull=False
                )
                if not ingredientes_validos.exists():
                    advertencias.append(
                        f"'{prep_borrador.nombre_preparacion}' omitida: sin ingredientes válidos."
                    )
                    continue

                prep_real = TablaPreparaciones.objects.create(
                    preparacion=prep_borrador.nombre_preparacion,
                    id_menu=menu,
                    id_componente=prep_borrador.componente_sugerido,
                )

                for ing_borrador in ingredientes_validos:
                    TablaPreparacionIngredientes.objects.create(
                        id_preparacion=prep_real,
                        id_ingrediente_siesa=ing_borrador.alimento_icbf,
                    )

                creadas += 1

            generacion.id_menu = menu
            generacion.estado = GeneracionIA.ESTADO_APROBADO
            generacion.fecha_aprobacion = timezone.now()
            generacion.usuario_aprobador = request.user
            generacion.save(update_fields=['id_menu', 'estado', 'fecha_aprobacion', 'usuario_aprobador'])

        RegistroActividad.registrar(
            request, 'agente', 'aprobar_borrador_ia',
            f"Modalidad {generacion.id_modalidad.modalidad} → Menú {menu.menu} — {creadas} preparaciones importadas"
        )

        return {'ok': True, 'preparaciones_creadas': creadas, 'advertencias': advertencias}

    except Exception as e:
        return {'ok': False, 'error': str(e)}
