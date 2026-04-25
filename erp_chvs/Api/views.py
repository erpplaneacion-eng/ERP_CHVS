from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import (
    SiesaCentroOperacion, SiesaInstalacion, SiesaTipoDocumento,
    SiesaUnidadNegocio, SiesaCentroCosto, SiesaProyecto,
    SiesaConcepto, SiesaMotivo, SiesaUbicacion,
    SiesaSolicitante, SiesaItem,
)


def _filas(queryset, campos):
    """Convierte un queryset en lista de filas (listas de strings) para el template."""
    rows = []
    for obj in queryset:
        row = []
        for campo in campos:
            val = getattr(obj, campo, '')
            if hasattr(val, 'strftime'):
                val = val.strftime('%d/%m/%Y %H:%M')
            row.append(val if val != '' else '—')
        rows.append(row)
    return rows


@login_required
def siesa_index(request):
    context = {
        'total_centros_operacion': SiesaCentroOperacion.objects.count(),
        'total_instalaciones': SiesaInstalacion.objects.count(),
        'total_tipos_documento': SiesaTipoDocumento.objects.count(),
        'total_unidades_negocio': SiesaUnidadNegocio.objects.count(),
        'total_centros_costo': SiesaCentroCosto.objects.count(),
        'total_proyectos': SiesaProyecto.objects.count(),
        'total_conceptos': SiesaConcepto.objects.count(),
        'total_motivos': SiesaMotivo.objects.count(),
        'total_ubicaciones': SiesaUbicacion.objects.count(),
        'total_solicitantes': SiesaSolicitante.objects.count(),
        'total_items': SiesaItem.objects.count(),
    }
    return render(request, 'Api/index.html', context)


@login_required
def lista_centros_operacion(request):
    campos = ['f285_id', 'f285_descripcion', 'fecha_sincronizacion']
    filas = _filas(SiesaCentroOperacion.objects.all().order_by('f285_id'), campos)
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Centros de Operación',
        'columnas': ['ID', 'Descripción', 'Sincronizado'],
        'filas': filas,
        'vacio_es_esperado': False,
        'page_length': 25,
    })


@login_required
def lista_instalaciones(request):
    campos = ['f157_id', 'f157_descripcion', 'f157_id_co', 'fecha_sincronizacion']
    filas = _filas(SiesaInstalacion.objects.all().order_by('f157_id'), campos)
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Instalaciones',
        'columnas': ['ID', 'Descripción', 'ID Centro Operación', 'Sincronizado'],
        'filas': filas,
        'vacio_es_esperado': False,
        'page_length': 25,
    })


@login_required
def lista_tipos_documento(request):
    campos = ['f021_id', 'f021_descripcion', 'fecha_sincronizacion']
    filas = _filas(SiesaTipoDocumento.objects.all().order_by('f021_id'), campos)
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Tipos de Documento',
        'columnas': ['ID', 'Descripción', 'Sincronizado'],
        'filas': filas,
        'vacio_es_esperado': False,
        'page_length': 25,
    })


@login_required
def lista_unidades_negocio(request):
    campos = ['f281_id', 'f281_descripcion', 'fecha_sincronizacion']
    filas = _filas(SiesaUnidadNegocio.objects.all().order_by('f281_id'), campos)
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Unidades de Negocio',
        'columnas': ['ID', 'Descripción', 'Sincronizado'],
        'filas': filas,
        'vacio_es_esperado': False,
        'page_length': 25,
    })


@login_required
def lista_centros_costo(request):
    campos = ['f284_id', 'f284_descripcion', 'f284_id_co', 'f284_id_un', 'fecha_sincronizacion']
    filas = _filas(SiesaCentroCosto.objects.all().order_by('f284_id'), campos)
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Centros de Costo',
        'columnas': ['ID', 'Descripción', 'ID Centro Operación', 'ID Unidad Negocio', 'Sincronizado'],
        'filas': filas,
        'vacio_es_esperado': False,
        'page_length': 25,
    })


@login_required
def lista_proyectos(request):
    campos = ['f107_id', 'f107_descripcion', 'f107_id_referencia', 'fecha_sincronizacion']
    filas = _filas(SiesaProyecto.objects.all().order_by('f107_id'), campos)
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Proyectos',
        'columnas': ['ID', 'Descripción', 'ID Referencia', 'Sincronizado'],
        'filas': filas,
        'vacio_es_esperado': False,
        'page_length': 50,
    })


@login_required
def lista_conceptos(request):
    campos = ['f145_id', 'f145_descripcion', 'f145_ind_naturaleza', 'f145_ind_liquidacion', 'fecha_sincronizacion']
    filas = _filas(SiesaConcepto.objects.all().order_by('f145_id'), campos)
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Conceptos',
        'columnas': ['ID', 'Descripción', 'Ind. Naturaleza', 'Ind. Liquidación', 'Sincronizado'],
        'filas': filas,
        'vacio_es_esperado': False,
        'page_length': 25,
    })


@login_required
def lista_motivos(request):
    campos = ['f146_id', 'f146_id_concepto', 'f146_ind_naturaleza', 'fecha_sincronizacion']
    filas = _filas(SiesaMotivo.objects.all().order_by('f146_id_concepto', 'f146_id'), campos)
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Motivos',
        'columnas': ['ID Motivo', 'ID Concepto', 'Ind. Naturaleza', 'Sincronizado'],
        'filas': filas,
        'vacio_es_esperado': False,
        'page_length': 25,
    })


@login_required
def lista_ubicaciones(request):
    campos = ['f155_id', 'f155_descripcion', 'f150_id', 'fecha_sincronizacion']
    filas = _filas(SiesaUbicacion.objects.all().order_by('f155_id'), campos)
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Ubicaciones / Bodegas',
        'columnas': ['ID', 'Descripción', 'ID f150', 'Sincronizado'],
        'filas': filas,
        'vacio_es_esperado': False,
        'page_length': 25,
    })


@login_required
def lista_solicitantes(request):
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Solicitantes',
        'columnas': [],
        'filas': [],
        'vacio_es_esperado': True,
        'page_length': 25,
    })


@login_required
def lista_items(request):
    return render(request, 'Api/catalogo_list.html', {
        'titulo': 'Items (Plan de Cuentas)',
        'columnas': [],
        'filas': [],
        'vacio_es_esperado': True,
        'page_length': 25,
    })
