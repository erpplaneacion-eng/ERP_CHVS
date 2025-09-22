# planeacion/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Programa
from .forms import ProgramaForm


@login_required
def planeacion_index(request):
    """
    Vista que muestra el dashboard principal del módulo de Planeación
    con tarjetas de acceso a las diferentes funcionalidades.
    """
    return render(request, 'planeacion/index.html')


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
