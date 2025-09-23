# principal/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
import json
from .models import PrincipalDepartamento, PrincipalMunicipio, TipoDocumento, TipoGenero, ModalidadesDeConsumo, NivelGradoEscolar
from planeacion.models import InstitucionesEducativas, SedesEducativas

def home(request):
    # Si el usuario ya está autenticado, redirigirlo al dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard') # Redirigir al dashboard usando namespace

    # Si no está autenticado, simplemente renderiza la página de inicio con el formulario de login
    return render(request, 'home.html')

@login_required
def principal_index(request):
    """Vista principal del módulo de configuración"""
    return render(request, 'principal/index.html')

@login_required
def lista_departamentos(request):
    """Vista para listar departamentos"""
    departamentos = PrincipalDepartamento.objects.all().order_by('nombre_departamento')
    paginator = Paginator(departamentos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'principal/departamentos.html', {
        'departamentos': page_obj,
        'total_departamentos': departamentos.count()
    })

@login_required
def lista_municipios(request):
    """Vista para listar municipios"""
    municipios = PrincipalMunicipio.objects.all().order_by('nombre_municipio')
    paginator = Paginator(municipios, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'principal/municipios.html', {
        'municipios': page_obj,
        'total_municipios': municipios.count()
    })

# API Views para AJAX
@login_required
@csrf_exempt
def api_departamentos(request):
    """API para manejar departamentos via AJAX"""
    if request.method == 'GET':
        departamentos = PrincipalDepartamento.objects.all().values(
            'codigo_departamento', 'nombre_departamento'
        )
        return JsonResponse({'departamentos': list(departamentos)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Verificar si ya existe un departamento con este código
            if PrincipalDepartamento.objects.filter(codigo_departamento=data['codigo_departamento']).exists():
                return JsonResponse({'success': False, 'error': 'Error: Ya existe un departamento con este código'})

            departamento = PrincipalDepartamento.objects.create(
                codigo_departamento=data['codigo_departamento'],
                nombre_departamento=data['nombre_departamento']
            )

            return JsonResponse({
                'success': True,
                'departamento': {
                    'codigo_departamento': departamento.codigo_departamento,
                    'nombre_departamento': departamento.nombre_departamento
                }
            })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Error: Ya existe un departamento con este código'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

@login_required
@csrf_exempt
def api_departamento_detail(request, codigo):
    """API para manejar un departamento específico"""
    departamento = get_object_or_404(PrincipalDepartamento, codigo_departamento=codigo)

    if request.method == 'GET':
        return JsonResponse({
            'codigo_departamento': departamento.codigo_departamento,
            'nombre_departamento': departamento.nombre_departamento
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            departamento.nombre_departamento = data['nombre_departamento']
            departamento.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            departamento.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

@login_required
@csrf_exempt
def api_municipios(request):
    """API para manejar municipios via AJAX"""
    if request.method == 'GET':
        municipios = PrincipalMunicipio.objects.all().values(
            'id', 'codigo_municipio', 'nombre_municipio', 'codigo_departamento'
        )
        return JsonResponse({'municipios': list(municipios)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Verificar si ya existe un municipio con este código en este departamento
            if PrincipalMunicipio.objects.filter(
                codigo_municipio=data['codigo_municipio'],
                codigo_departamento=data['codigo_departamento']
            ).exists():
                return JsonResponse({'success': False, 'error': 'Error: Ya existe un municipio con este código en este departamento'})

            municipio = PrincipalMunicipio.objects.create(
                codigo_municipio=data['codigo_municipio'],
                nombre_municipio=data['nombre_municipio'],
                codigo_departamento=data['codigo_departamento']
            )

            return JsonResponse({
                'success': True,
                'municipio': {
                    'id': municipio.id,
                    'codigo_municipio': municipio.codigo_municipio,
                    'nombre_municipio': municipio.nombre_municipio,
                    'codigo_departamento': municipio.codigo_departamento
                }
            })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Error: Ya existe un municipio con este código en este departamento'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

@login_required
@csrf_exempt
def api_municipio_detail(request, id):
    """API para manejar un municipio específico"""
    municipio = get_object_or_404(PrincipalMunicipio, id=id)

    if request.method == 'GET':
        return JsonResponse({
            'id': municipio.id,
            'codigo_municipio': municipio.codigo_municipio,
            'nombre_municipio': municipio.nombre_municipio,
            'codigo_departamento': municipio.codigo_departamento
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            municipio.codigo_municipio = data['codigo_municipio']
            municipio.nombre_municipio = data['nombre_municipio']
            municipio.codigo_departamento = data['codigo_departamento']
            municipio.save()
            return JsonResponse({'success': True})
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Error: Ya existe un municipio con este código'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            municipio.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# ===== VISTAS PARA TIPOS DE DOCUMENTO =====
@login_required
def lista_tipos_documento(request):
    """Vista para listar tipos de documento"""
    tipos_documento = TipoDocumento.objects.all().order_by('tipo_documento')
    paginator = Paginator(tipos_documento, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'principal/tipos_documento.html', {
        'tipos_documento': page_obj,
        'total_tipos_documento': tipos_documento.count()
    })

@login_required
@csrf_exempt
def api_tipos_documento(request):
    """API para manejar tipos de documento via AJAX"""
    if request.method == 'GET':
        tipos_documento = TipoDocumento.objects.all().values(
            'id_documento', 'tipo_documento', 'codigo_documento'
        )
        return JsonResponse({'tipos_documento': list(tipos_documento)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Verificar si ya existe un tipo de documento con este ID
            if TipoDocumento.objects.filter(id_documento=data['id_documento']).exists():
                return JsonResponse({'success': False, 'error': 'Error: Ya existe un tipo de documento con este ID'})

            tipo_documento = TipoDocumento.objects.create(
                id_documento=data['id_documento'],
                tipo_documento=data['tipo_documento'],
                codigo_documento=data['codigo_documento']
            )

            return JsonResponse({
                'success': True,
                'tipo_documento': {
                    'id_documento': tipo_documento.id_documento,
                    'tipo_documento': tipo_documento.tipo_documento,
                    'codigo_documento': tipo_documento.codigo_documento
                }
            })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Error: Ya existe un tipo de documento con este ID'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

@login_required
@csrf_exempt
def api_tipo_documento_detail(request, id_documento):
    """API para manejar un tipo de documento específico"""
    tipo_documento = get_object_or_404(TipoDocumento, id_documento=id_documento)

    if request.method == 'GET':
        return JsonResponse({
            'id_documento': tipo_documento.id_documento,
            'tipo_documento': tipo_documento.tipo_documento,
            'codigo_documento': tipo_documento.codigo_documento
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            tipo_documento.tipo_documento = data['tipo_documento']
            tipo_documento.codigo_documento = data['codigo_documento']
            tipo_documento.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            tipo_documento.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# ===== VISTAS PARA TIPOS DE GÉNERO =====
@login_required
def lista_tipos_genero(request):
    """Vista para listar tipos de género"""
    tipos_genero = TipoGenero.objects.all().order_by('genero')
    paginator = Paginator(tipos_genero, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'principal/tipos_genero.html', {
        'tipos_genero': page_obj,
        'total_tipos_genero': tipos_genero.count()
    })

@login_required
@csrf_exempt
def api_tipos_genero(request):
    """API para manejar tipos de género via AJAX"""
    if request.method == 'GET':
        tipos_genero = TipoGenero.objects.all().values(
            'id_genero', 'genero', 'codigo_genero'
        )
        return JsonResponse({'tipos_genero': list(tipos_genero)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Verificar si ya existe un tipo de género con este ID
            if TipoGenero.objects.filter(id_genero=data['id_genero']).exists():
                return JsonResponse({'success': False, 'error': 'Error: Ya existe un tipo de género con este ID'})

            tipo_genero = TipoGenero.objects.create(
                id_genero=data['id_genero'],
                genero=data['genero'],
                codigo_genero=data['codigo_genero']
            )

            return JsonResponse({
                'success': True,
                'tipo_genero': {
                    'id_genero': tipo_genero.id_genero,
                    'genero': tipo_genero.genero,
                    'codigo_genero': tipo_genero.codigo_genero
                }
            })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Error: Ya existe un tipo de género con este ID'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

@login_required
@csrf_exempt
def api_tipo_genero_detail(request, id_genero):
    """API para manejar un tipo de género específico"""
    tipo_genero = get_object_or_404(TipoGenero, id_genero=id_genero)

    if request.method == 'GET':
        return JsonResponse({
            'id_genero': tipo_genero.id_genero,
            'genero': tipo_genero.genero,
            'codigo_genero': tipo_genero.codigo_genero
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            tipo_genero.genero = data['genero']
            tipo_genero.codigo_genero = data['codigo_genero']
            tipo_genero.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            tipo_genero.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# ===== VISTAS PARA MODALIDADES DE CONSUMO =====
@login_required
def lista_modalidades_consumo(request):
    """Vista para listar modalidades de consumo"""
    modalidades = ModalidadesDeConsumo.objects.all().order_by('modalidad')
    paginator = Paginator(modalidades, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'principal/modalidades_consumo.html', {
        'modalidades': page_obj,
        'total_modalidades': modalidades.count()
    })

@login_required
@csrf_exempt
def api_modalidades_consumo(request):
    """API para manejar modalidades de consumo via AJAX"""
    if request.method == 'GET':
        modalidades = ModalidadesDeConsumo.objects.all().values(
            'id_modalidades', 'modalidad', 'cod_modalidad'
        )
        return JsonResponse({'modalidades': list(modalidades)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Verificar si ya existe una modalidad con este ID
            if ModalidadesDeConsumo.objects.filter(id_modalidades=data['id_modalidades']).exists():
                return JsonResponse({'success': False, 'error': 'Error: Ya existe una modalidad con este ID'})

            modalidad = ModalidadesDeConsumo.objects.create(
                id_modalidades=data['id_modalidades'],
                modalidad=data['modalidad'],
                cod_modalidad=data['cod_modalidad']
            )

            return JsonResponse({
                'success': True,
                'modalidad': {
                    'id_modalidades': modalidad.id_modalidades,
                    'modalidad': modalidad.modalidad,
                    'cod_modalidad': modalidad.cod_modalidad
                }
            })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Error: Ya existe una modalidad con este ID'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

@login_required
@csrf_exempt
def api_modalidad_consumo_detail(request, id_modalidades):
    """API para manejar una modalidad de consumo específica"""
    modalidad = get_object_or_404(ModalidadesDeConsumo, id_modalidades=id_modalidades)

    if request.method == 'GET':
        return JsonResponse({
            'id_modalidades': modalidad.id_modalidades,
            'modalidad': modalidad.modalidad,
            'cod_modalidad': modalidad.cod_modalidad
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            modalidad.modalidad = data['modalidad']
            modalidad.cod_modalidad = data['cod_modalidad']
            modalidad.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            modalidad.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# ===== VISTAS PARA INSTITUCIONES EDUCATIVAS =====
@login_required
def lista_instituciones(request):
    """Vista para listar instituciones educativas"""
    instituciones = InstitucionesEducativas.objects.select_related('id_municipios').all().order_by('nombre_institucion')
    paginator = Paginator(instituciones, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'principal/instituciones.html', {
        'instituciones': page_obj,
        'total_instituciones': instituciones.count()
    })

@login_required
@csrf_exempt
def api_instituciones(request):
    """API para manejar instituciones educativas via AJAX"""
    if request.method == 'GET':
        instituciones = InstitucionesEducativas.objects.select_related('id_municipios').all().values(
            'codigo_ie', 'nombre_institucion', 'id_municipios__nombre_municipio'
        )
        return JsonResponse({'instituciones': list(instituciones)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Verificar si ya existe una institución con este código IE
            if InstitucionesEducativas.objects.filter(codigo_ie=data['codigo_ie']).exists():
                return JsonResponse({'success': False, 'error': 'Error: Ya existe una institución con este código IE'})

            institucion = InstitucionesEducativas.objects.create(
                codigo_ie=data['codigo_ie'],
                nombre_institucion=data['nombre_institucion'],
                id_municipios_id=data['id_municipios']
            )

            return JsonResponse({
                'success': True,
                'institucion': {
                    'codigo_ie': institucion.codigo_ie,
                    'nombre_institucion': institucion.nombre_institucion,
                    'municipio': institucion.id_municipios.nombre_municipio
                }
            })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Error: Ya existe una institución con este código IE'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

@login_required
@csrf_exempt
def api_institucion_detail(request, codigo_ie):
    """API para manejar una institución educativa específica"""
    institucion = get_object_or_404(InstitucionesEducativas, codigo_ie=codigo_ie)

    if request.method == 'GET':
        return JsonResponse({
            'codigo_ie': institucion.codigo_ie,
            'nombre_institucion': institucion.nombre_institucion,
            'id_municipios': institucion.id_municipios.id
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            institucion.nombre_institucion = data['nombre_institucion']
            institucion.id_municipios_id = data['id_municipios']
            institucion.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            institucion.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# ===== VISTAS PARA SEDES EDUCATIVAS =====
@login_required
def lista_sedes(request):
    """Vista para listar sedes educativas"""
    sedes = SedesEducativas.objects.select_related('codigo_ie').all().order_by('codigo_ie__nombre_institucion', 'nombre_sede_educativa')
    paginator = Paginator(sedes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'principal/sedes.html', {
        'sedes': page_obj,
        'total_sedes': sedes.count()
    })

@login_required
@csrf_exempt
def api_sedes(request):
    """API para manejar sedes educativas via AJAX"""
    if request.method == 'GET':
        sedes = SedesEducativas.objects.select_related('codigo_ie').all().values(
            'cod_interprise', 'cod_dane', 'nombre_sede_educativa', 'nombre_generico_sede', 'codigo_ie__codigo_ie', 'codigo_ie__nombre_institucion',
            'direccion', 'zona', 'preparado', 'industrializado'
        )
        return JsonResponse({'sedes': list(sedes)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Verificar si ya existe una sede con este código
            if SedesEducativas.objects.filter(cod_interprise=data['cod_interprise']).exists():
                return JsonResponse({'success': False, 'error': 'Error: Ya existe una sede con este código'})

            sede = SedesEducativas.objects.create(
                cod_interprise=data['cod_interprise'],
                cod_dane=data['cod_dane'],
                nombre_sede_educativa=data['nombre_sede_educativa'],
                nombre_generico_sede=data.get('nombre_generico_sede', 'Sin especificar'),
                codigo_ie_id=data['codigo_ie'],
                direccion=data.get('direccion', ''),
                zona=data['zona'],
                preparado=data['preparado'],
                industrializado=data['industrializado']
            )

            return JsonResponse({
                'success': True,
                'sede': {
                    'cod_interprise': sede.cod_interprise,
                    'nombre_sede_educativa': sede.nombre_sede_educativa,
                    'institucion': sede.codigo_ie.nombre_institucion,
                    'zona': sede.zona
                }
            })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Error: Ya existe una sede con este código'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

@login_required
@csrf_exempt
def api_sede_detail(request, cod_interprise):
    """API para manejar una sede educativa específica"""
    sede = get_object_or_404(SedesEducativas, cod_interprise=cod_interprise)

    if request.method == 'GET':
        return JsonResponse({
            'cod_interprise': sede.cod_interprise,
            'cod_dane': sede.cod_dane,
            'nombre_sede_educativa': sede.nombre_sede_educativa,
            'nombre_generico_sede': sede.nombre_generico_sede,
            'codigo_ie': sede.codigo_ie.codigo_ie,
            'direccion': sede.direccion,
            'zona': sede.zona,
            'preparado': sede.preparado,
            'industrializado': sede.industrializado
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            sede.cod_dane = data['cod_dane']
            sede.nombre_sede_educativa = data['nombre_sede_educativa']
            sede.nombre_generico_sede = data.get('nombre_generico_sede', 'Sin especificar')
            sede.codigo_ie_id = data['codigo_ie']
            sede.direccion = data.get('direccion', '')
            sede.zona = data['zona']
            sede.preparado = data['preparado']
            sede.industrializado = data['industrializado']
            sede.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            sede.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# =================== NIVELES GRADO ESCOLAR ===================

@login_required
def lista_niveles_grado(request):
    """Vista para mostrar el listado de niveles grado escolar."""
    total_niveles_grado = NivelGradoEscolar.objects.count()
    return render(request, 'principal/niveles_grado.html', {
        'total_niveles_grado': total_niveles_grado
    })


@csrf_exempt
def api_niveles_grado(request):
    """API para gestionar niveles grado escolar (GET, POST)."""

    if request.method == 'GET':
        niveles_grado = NivelGradoEscolar.objects.all().order_by('id_grado_escolar')

        # Implementar paginación si se especifica
        page = request.GET.get('page')
        if page:
            paginator = Paginator(niveles_grado, 10)  # 10 items por página
            niveles_grado = paginator.get_page(page)

            data = {
                'results': [
                    {
                        'id_grado_escolar': nivel.id_grado_escolar,
                        'grados_sedes': nivel.grados_sedes,
                        'nivel_escolar_uapa': nivel.nivel_escolar_uapa,
                    }
                    for nivel in niveles_grado
                ],
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': niveles_grado.number,
                'has_next': niveles_grado.has_next(),
                'has_previous': niveles_grado.has_previous()
            }
        else:
            # Sin paginación, devolver todos los resultados
            data = [
                {
                    'id_grado_escolar': nivel.id_grado_escolar,
                    'grados_sedes': nivel.grados_sedes,
                    'nivel_escolar_uapa': nivel.nivel_escolar_uapa,
                }
                for nivel in niveles_grado
            ]

        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            nivel_grado = NivelGradoEscolar(
                id_grado_escolar=data['id_grado_escolar'],
                grados_sedes=data['grados_sedes'],
                nivel_escolar_uapa=data['nivel_escolar_uapa']
            )
            nivel_grado.save()
            return JsonResponse({
                'success': True,
                'id_grado_escolar': nivel_grado.id_grado_escolar,
                'grados_sedes': nivel_grado.grados_sedes,
                'nivel_escolar_uapa': nivel_grado.nivel_escolar_uapa,
            })
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'El ID de grado escolar ya existe'})
        except KeyError as e:
            return JsonResponse({'success': False, 'error': f'Campo requerido faltante: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al crear: {str(e)}'})


@csrf_exempt
def api_nivel_grado_detail(request, id_grado_escolar):
    """API para gestionar un nivel grado escolar específico (GET, PUT, DELETE)."""

    try:
        nivel_grado = get_object_or_404(NivelGradoEscolar, pk=id_grado_escolar)
    except:
        return JsonResponse({'success': False, 'error': 'Nivel grado no encontrado'})

    if request.method == 'GET':
        return JsonResponse({
            'id_grado_escolar': nivel_grado.id_grado_escolar,
            'grados_sedes': nivel_grado.grados_sedes,
            'nivel_escolar_uapa': nivel_grado.nivel_escolar_uapa,
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            nivel_grado.grados_sedes = data['grados_sedes']
            nivel_grado.nivel_escolar_uapa = data['nivel_escolar_uapa']
            nivel_grado.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            nivel_grado.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})