from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def costos_index(request):
    """
    Vista principal del módulo de costos.
    """
    return render(request, 'costos/index.html')
