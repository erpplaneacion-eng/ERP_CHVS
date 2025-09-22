from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import TablaAlimentos2018Icbf
from .forms import AlimentoForm

# @login_required ya no es necesario si usamos @permission_required, ya que este último ya lo comprueba.
@permission_required('nutricion.view_contenido_nutricion', login_url='/dashboard/')
def nutricion_index(request):
    return render(request, 'nutricion/index.html')

@permission_required('nutricion.view_contenido_nutricion', login_url='/dashboard/')
def lista_alimentos(request):
    # Manejo de POST para crear un nuevo alimento
    if request.method == 'POST':
        form = AlimentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('nutricion:lista_alimentos')
    else:
        form = AlimentoForm()
    
    # Búsqueda
    search_query = request.GET.get('q', '')
    alimentos_list = TablaAlimentos2018Icbf.objects.all().order_by('nombre_del_alimento')
    
    if search_query:
        alimentos_list = alimentos_list.filter(
            Q(nombre_del_alimento__icontains=search_query) |
            Q(codigo__icontains=search_query)
        )
    
    # Paginación
    paginator = Paginator(alimentos_list, 20)
    page_number = request.GET.get('page')
    alimentos_page = paginator.get_page(page_number)
    
    context = {
        'alimentos_page': alimentos_page,
        'search_query': search_query,
        'form': form,
    }
    
    return render(request, 'nutricion/lista_alimentos.html', context)

@permission_required('nutricion.view_contenido_nutricion', login_url='/dashboard/')
def editar_alimento(request, codigo):
    alimento_a_editar = get_object_or_404(TablaAlimentos2018Icbf, pk=codigo)
    
    if request.method == 'POST':
        form = AlimentoForm(request.POST, instance=alimento_a_editar)
        if form.is_valid():
            form.save()
            return redirect('nutricion:lista_alimentos')
    
    return redirect('nutricion:lista_alimentos')