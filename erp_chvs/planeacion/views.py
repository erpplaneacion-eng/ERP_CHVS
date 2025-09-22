# planeacion/views.py
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import InformacionCodindem, Programa
from .forms import ProgramaForm, ComedorForm
from collections import defaultdict  # <-- Importación necesaria para el resumen anidado


@login_required
def planeacion_index(request):
    """
    Vista que muestra el dashboard principal del módulo de Planeación
    con tarjetas de acceso a las diferentes funcionalidades.
    """
    return render(request, 'planeacion/index.html')


@login_required
def lista_comedores(request):
    # Manejo de POST para crear un nuevo comedor
    if request.method == 'POST':
        form = ComedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('planeacion:lista_comedores')
    else:
        form = ComedorForm()
        
    # Búsqueda
    search_query = request.GET.get('q', '')
    comedores_list = InformacionCodindem.objects.all().order_by('departamento', 'municipio', 'sede')
    
    if search_query:
        comedores_list = comedores_list.filter(
            Q(institucion__icontains=search_query) |
            Q(sede__icontains=search_query) |
            Q(municipio__icontains=search_query)
        )
        
    # --- Lógica del resumen por departamento y municipio ---
    nested_summary = {}
    
    # Obtener todos los comedores para el resumen (sin filtro de búsqueda)
    all_comedores = InformacionCodindem.objects.all()
    total_registros = all_comedores.count()
    
    if total_registros > 0:
        # Conteo manual por departamento y municipio
        contador_departamentos = {}
        
        for comedor in all_comedores:
            # Normalizar nombres (manejar None y espacios)
            dept = (comedor.departamento or "").strip() or "SIN DEPARTAMENTO"
            municipio = (comedor.municipio or "").strip() or "SIN MUNICIPIO"
            
            # Crear estructura si no existe
            if dept not in contador_departamentos:
                contador_departamentos[dept] = {}
            
            if municipio not in contador_departamentos[dept]:
                contador_departamentos[dept][municipio] = 0
            
            contador_departamentos[dept][municipio] += 1
        
        # Convertir al formato esperado por el template
        for departamento, municipios_dict in contador_departamentos.items():
            nested_summary[departamento] = []
            for municipio, total in municipios_dict.items():
                nested_summary[departamento].append({
                    'municipio': municipio,
                    'total': total
                })
            # Ordenar municipios por nombre
            nested_summary[departamento].sort(key=lambda x: x['municipio'])

    # Paginación
    paginator = Paginator(comedores_list, 10)
    page_number = request.GET.get('page')
    comedores_page = paginator.get_page(page_number)

    context = {
        'comedores_page': comedores_page,
        'nested_summary': nested_summary,  # <-- Ahora usamos el resumen anidado
        'search_query': search_query,
        'form': form,
    }
    return render(request, 'planeacion/lista_comedores.html', context)


@login_required
def editar_comedor(request, pk):
    comedor_a_editar = get_object_or_404(InformacionCodindem, pk=pk)
    
    if request.method == 'POST':
        form = ComedorForm(request.POST, instance=comedor_a_editar)
        if form.is_valid():
            form.save()
            return redirect('planeacion:lista_comedores')
    
    return redirect('planeacion:lista_comedores')


@login_required
def lista_programas(request):
    if request.method == 'POST':
        form = ProgramaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('planeacion:lista_programas')
    else:
        form = ProgramaForm()

    programas = Programa.objects.all().order_by('-fecha_inicial')
    
    context = {
        'programas': programas,
        'form': form, 
    }
    return render(request, 'planeacion/lista_programas.html', context)


@login_required
def editar_programa(request, pk):
    programa_a_editar = get_object_or_404(Programa, pk=pk)
    
    if request.method == 'POST':
        form = ProgramaForm(request.POST, request.FILES, instance=programa_a_editar)
        if form.is_valid():
            form.save()
            return redirect('planeacion:lista_programas')
    
    return redirect('planeacion:lista_programas')
