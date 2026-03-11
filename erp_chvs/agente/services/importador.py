from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from nutricion.models import TablaMenus, TablaPreparaciones, TablaPreparacionIngredientes
from principal.models import RegistroActividad

from ..models import GeneracionIA, BorradorPreparacionIA, BorradorIngredienteIA
from .inicializador_niveles import inicializar_niveles_para_menu


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

    # Prefetch con select_related profundo para evitar N+1 en la resolución de
    # componentes y grupos desde el catálogo ICBF
    preparaciones_borrador = BorradorPreparacionIA.objects.filter(
        generacion=generacion,
    ).select_related(
        'componente_sugerido__id_grupo_alimentos',
    ).prefetch_related(
        Prefetch(
            'ingredientes',
            queryset=BorradorIngredienteIA.objects.select_related(
                'alimento_icbf__id_componente__id_grupo_alimentos',
            ),
        ),
    )

    creadas = 0
    advertencias = []
    # Acumula (prep_real, ing_prep_real, alimento_icbf) para el inicializador de niveles
    items_nivel = []

    try:
        with transaction.atomic():
            for prep_borrador in preparaciones_borrador:
                if prep_borrador.estado_validacion == BorradorPreparacionIA.INVALIDA:
                    advertencias.append(
                        f"'{prep_borrador.nombre_preparacion}' omitida: marcada como inválida."
                    )
                    continue

                ingredientes_validos = [
                    ing for ing in prep_borrador.ingredientes.all()
                    if ing.estado_validacion == BorradorIngredienteIA.VALIDO
                    and ing.alimento_icbf is not None
                ]
                if not ingredientes_validos:
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
                    alimento_icbf = ing_borrador.alimento_icbf

                    # Resolver componente: ICBF propio → fallback preparación
                    componente = alimento_icbf.id_componente or prep_borrador.componente_sugerido
                    # Resolver grupo desde el componente resuelto
                    grupo = componente.id_grupo_alimentos if componente else None

                    ing_prep_real = TablaPreparacionIngredientes.objects.create(
                        id_preparacion=prep_real,
                        id_ingrediente_siesa=alimento_icbf,
                        id_componente=componente,
                        id_grupo_alimentos=grupo,
                    )
                    items_nivel.append((prep_real, ing_prep_real, alimento_icbf))

                creadas += 1

            # Inicializar análisis nutricional por los 5 niveles educativos
            inicializar_niveles_para_menu(menu, generacion.id_modalidad, items_nivel)

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
