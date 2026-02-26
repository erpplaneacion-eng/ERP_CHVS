from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def logistica_principal(request):
    """
    Vista principal del módulo de logística.
    Muestra los accesos rápidos (cards) a las rutas, tipos de rutas y asignación de sedes.
    """
    return render(request, 'logistica/index.html')
