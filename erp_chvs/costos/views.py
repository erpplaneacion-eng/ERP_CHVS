from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from nutricion.models import (
    TablaMenus, TablaPreparaciones, TablaPreparacionIngredientes, 
    TablaIngredientesPorNivel, TablaAlimentos2018Icbf
)
from principal.models import PrincipalMunicipio, TablaGradosEscolaresUapa
from planeacion.models import Programa
from django.db.models import Q

@login_required
def costos_index(request):
    """
    Vista principal del módulo de costos.
    """
    return render(request, 'costos/index.html')

@login_required
def matriz_nutricional(request):
    """
    Vista de la Matriz Nutricional con información de ingredientes, pesos y niveles.
    """
    # Filtros
    municipio_id = request.GET.get('municipio')
    programa_id = request.GET.get('programa')
    
    municipios = PrincipalMunicipio.objects.all().order_by('nombre_municipio')
    programas = Programa.objects.all().order_by('programa')
    
    if municipio_id:
        programas = programas.filter(municipio_id=municipio_id)

    # Consulta base: Empezamos por los análisis guardados (que tienen los pesos por nivel)
    # Si no hay análisis, la matriz estaría vacía para ese nivel.
    # Pero el usuario quiere ver la estructura MODALIDAD | NIVEL | SEMANA | MENU | PREPARACION | INGREDIENTE
    
    # Obtenemos los ingredientes configurados por nivel
    queryset = TablaIngredientesPorNivel.objects.select_related(
        'id_analisis__id_menu__id_modalidad',
        'id_analisis__id_menu__id_contrato',
        'id_analisis__id_nivel_escolar_uapa',
        'id_preparacion',
    ).all()

    if municipio_id:
        queryset = queryset.filter(id_analisis__id_menu__id_contrato__municipio_id=municipio_id)
    
    if programa_id:
        queryset = queryset.filter(id_analisis__id_menu__id_contrato_id=programa_id)

    # Ordenamiento solicitado
    queryset = queryset.order_by(
        'id_analisis__id_menu__id_modalidad__modalidad',
        'id_analisis__id_nivel_escolar_uapa__nivel_escolar_uapa',
        'id_analisis__id_menu__semana',
        'id_analisis__id_menu__menu',
        'id_preparacion__preparacion'
    )

    # Para los ingredientes, necesitamos el nombre del alimento ICBF
    # El modelo TablaIngredientesPorNivel tiene codigo_icbf
    # Vamos a crear una lista de diccionarios para facilitar el renderizado
    
    # Optimización: Obtener todos los nombres ICBF de una vez
    codigos_icbf = queryset.values_list('codigo_icbf', flat=True).distinct()
    alimentos_dict = {a.codigo: a.nombre_del_alimento for a in TablaAlimentos2018Icbf.objects.filter(codigo__in=codigos_icbf)}

    matriz_data = []
    for item in queryset:
        matriz_data.append({
            'modalidad': item.id_analisis.id_menu.id_modalidad.modalidad,
            'nivel_escolar': item.id_analisis.id_nivel_escolar_uapa.nivel_escolar_uapa,
            'semana': item.id_analisis.id_menu.semana or 'N/A',
            'menu': item.id_analisis.id_menu.menu,
            'preparacion': item.id_preparacion.preparacion,
            'ingrediente': alimentos_dict.get(item.codigo_icbf, item.codigo_icbf),
            'peso_bruto': item.peso_bruto,
            'peso_neto': item.peso_neto,
        })

    context = {
        'municipios': municipios,
        'programas': programas,
        'matriz_data': matriz_data,
        'selected_municipio': municipio_id,
        'selected_programa': programa_id,
    }
    
    return render(request, 'costos/matriz_nutricional.html', context)
