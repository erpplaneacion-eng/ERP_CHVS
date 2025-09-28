"""
Servicio dedicado para la generación de PDFs de asistencia.
Separado del views.py para mantener la organización del código.
"""

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import os
from io import BytesIO
import zipfile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import ListadosFocalizacion
from principal.models import PrincipalDepartamento, PrincipalMunicipio
from planeacion.models import SedesEducativas, Programa
from .pdf_generator import crear_formato_asistencia
from .logging_config import FacturacionLogger


class PDFAsistenciaService:
    """
    Servicio para manejar la generación de PDFs de asistencia.
    """

    @staticmethod
    def obtener_datos_geograficos(primer_estudiante):
        """
        Obtiene los datos geográficos (departamento, municipio, códigos DANE)
        a partir del primer estudiante encontrado.

        Args:
            primer_estudiante: Instancia de ListadosFocalizacion

        Returns:
            dict: Diccionario con datos geográficos
        """
        nombre_municipio_etc = primer_estudiante.etc
        departamento_obj = None
        dane_departamento = 'N/A'
        dane_municipio = 'N/A'

        try:
            # Buscar el municipio en la tabla principal usando el nombre del ETC
            municipio_principal_obj = PrincipalMunicipio.objects.get(
                nombre_municipio__iexact=nombre_municipio_etc
            )
            dane_municipio = municipio_principal_obj.codigo_municipio

            # A partir del municipio, encontrar el departamento
            departamento_obj = PrincipalDepartamento.objects.get(
                codigo_departamento=municipio_principal_obj.codigo_departamento
            )
            dane_departamento = departamento_obj.codigo_departamento

        except (PrincipalMunicipio.DoesNotExist, PrincipalDepartamento.DoesNotExist):
            # Si no se encuentra, los valores se quedan como 'N/A'
            pass

        return {
            'nombre_municipio_etc': nombre_municipio_etc,
            'departamento_obj': departamento_obj,
            'dane_departamento': dane_departamento,
            'dane_municipio': dane_municipio
        }

    @staticmethod
    def obtener_dane_institucion(nombre_sede_focalizacion):
        """
        Obtiene el código DANE de la institución educativa.

        Args:
            nombre_sede_focalizacion: Nombre de la sede de focalización

        Returns:
            str: Código DANE de la institución o mensaje de error
        """
        try:
            sede_info_dane = SedesEducativas.objects.get(
                nombre_sede_educativa=nombre_sede_focalizacion
            )
            return sede_info_dane.cod_dane
        except SedesEducativas.DoesNotExist:
            return 'DANE no encontrado'

    @staticmethod
    def identificar_complementos_presentes(estudiantes_sede):
        """
        Identifica los códigos de complemento únicos presentes en los estudiantes.

        Args:
            estudiantes_sede: QuerySet de estudiantes

        Returns:
            set: Conjunto de códigos de complemento presentes
        """
        mapeo_codigos = {
            "CAP AM": "CAJMPS",
            "CAP PM": "CAJTPS",
            "Almuerzo JU": "ALMUERZO",
            "Refuerzo": "RCPS"
        }

        codigos_presentes = set()
        for est in estudiantes_sede:
            for comp_amigable in est.complementos_activos:
                if comp_amigable in mapeo_codigos:
                    codigos_presentes.add(mapeo_codigos[comp_amigable])

        return codigos_presentes, mapeo_codigos

    @staticmethod
    def construir_datos_encabezado(datos_geograficos, nombre_sede_focalizacion,
                                 dane_ie, programa_obj, mes, ano, codigo):
        """
        Construye el diccionario con los datos del encabezado del PDF.

        Args:
            datos_geograficos: Dict con datos geográficos
            nombre_sede_focalizacion: Nombre de la sede
            dane_ie: Código DANE de la institución
            programa_obj: Objeto programa
            mes: Mes de atención
            ano: Año
            codigo: Código del complemento

        Returns:
            dict: Datos del encabezado
        """
        # Obtener la ruta del logo desde el programa
        ruta_logo_final = None
        if programa_obj and programa_obj.imagen:
            ruta_logo_final = programa_obj.imagen.path

        return {
            'departamento': str(datos_geograficos['departamento_obj'].nombre_departamento) if datos_geograficos['departamento_obj'] else 'N/A',
            'institucion': str(nombre_sede_focalizacion),
            'municipio': str(datos_geograficos['nombre_municipio_etc']),
            'dane_ie': str(dane_ie),
            'operador': str(programa_obj.programa) if programa_obj else 'N/A',
            'contrato': str(programa_obj.contrato) if programa_obj else 'N/A',
            'mes': str(mes).upper(),
            'ano': str(ano),
            'dane_departamento': str(datos_geograficos['dane_departamento']),
            'dane_municipio': str(datos_geograficos['dane_municipio']),
            'codigo_complemento': str(codigo),
            'ruta_logo': ruta_logo_final
        }

    @staticmethod
    def generar_pdf_asistencia(sede_cod_interprise, mes, focalizacion):
        """
        Genera los PDFs de asistencia para una sede, mes y focalización específicos.
        Lógica de negocio para generar los PDFs de asistencia para una sede, mes y focalización.
        Crea un archivo ZIP con un PDF por cada tipo de complemento.

        Args:
            sede_cod_interprise: Código interprise de la sede
            mes: Mes de atención
            focalizacion: Focalización

        Returns:
            HttpResponse: Respuesta con el archivo ZIP o mensaje de error
        """
        try:
            # Buscar sede
            sede_obj = get_object_or_404(SedesEducativas.objects.select_related(
                'codigo_ie__id_municipios'
            ), cod_interprise=sede_cod_interprise)

            # Buscar programa
            programa_obj = Programa.objects.filter(
                municipio=sede_obj.codigo_ie.id_municipios,
                estado='activo'
            ).first()

            # Buscar estudiantes
            estudiantes_sede = ListadosFocalizacion.objects.filter(
                sede=sede_obj.nombre_sede_educativa,
                focalizacion=focalizacion
            ).order_by('apellido1', 'apellido2', 'nombre1')

            if not estudiantes_sede.exists():
                return HttpResponse(
                    f"No se encontraron estudiantes para la sede {sede_obj.nombre_sede_educativa} con la focalización '{focalizacion}'.",
                    status=404
                )
                return HttpResponse(f"No se encontraron estudiantes para la sede {sede_obj.nombre_sede_educativa} con la focalización '{focalizacion}'.", status=404)

            # Obtener datos geográficos del primer estudiante
            primer_estudiante = estudiantes_sede.first()
            datos_geograficos = PDFAsistenciaService.obtener_datos_geograficos(primer_estudiante)
            nombre_municipio_etc = primer_estudiante.etc

            # Obtener datos adicionales
            departamento_obj = None
            dane_departamento = 'N/A'
            dane_municipio = 'N/A'

            try:
                municipio_principal_obj = PrincipalMunicipio.objects.get(nombre_municipio__iexact=nombre_municipio_etc)
                dane_municipio = municipio_principal_obj.codigo_municipio
                departamento_obj = PrincipalDepartamento.objects.get(codigo_departamento=municipio_principal_obj.codigo_departamento)
                dane_departamento = departamento_obj.codigo_departamento
            except (PrincipalMunicipio.DoesNotExist, PrincipalDepartamento.DoesNotExist):
                pass

            programa_obj = Programa.objects.filter(
                municipio__nombre_municipio__iexact=nombre_municipio_etc,
                estado='activo'
            ).first()

            nombre_sede_focalizacion = primer_estudiante.sede
            dane_ie = PDFAsistenciaService.obtener_dane_institucion(nombre_sede_focalizacion)
            try:
                sede_info_dane = SedesEducativas.objects.get(nombre_sede_educativa=nombre_sede_focalizacion)
                dane_ie = sede_info_dane.cod_dane
            except SedesEducativas.DoesNotExist:
                dane_ie = 'DANE no encontrado'

            ano = primer_estudiante.ano

            if not ano:
                return HttpResponse(
                    f"No se pudo determinar el año para la focalización '{focalizacion}'.",
                    status=404
                )
                return HttpResponse(f"No se pudo determinar el año para la focalización '{focalizacion}'.", status=404)

            # Identificar complementos presentes
            codigos_presentes, mapeo_codigos = PDFAsistenciaService.identificar_complementos_presentes(estudiantes_sede)
            mapeo_codigos = {
                "CAP AM": "CAJMPS", "CAP PM": "CAJTPS",
                "Almuerzo JU": "ALMUERZO", "Refuerzo": "RCPS"
            }

            codigos_presentes = set()
            for est in estudiantes_sede:
                for comp_amigable in est.complementos_activos:
                    if comp_amigable in mapeo_codigos:
                        codigos_presentes.add(mapeo_codigos[comp_amigable])

            if not codigos_presentes:
                return HttpResponse(
                    "No hay estudiantes con complementos asignados en esta sede.",
                    status=404
                )
                return HttpResponse("No hay estudiantes con complementos asignados en esta sede.", status=404)

            # Crear ZIP con PDFs
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                for codigo in codigos_presentes:
                    # Encontrar el nombre amigable correspondiente al código
                    nombre_amigable_actual = next(
                        (key for key, value in mapeo_codigos.items() if value == codigo),
                        None
                    )
                    nombre_amigable_actual = next((key for key, value in mapeo_codigos.items() if value == codigo), None)
                    if not nombre_amigable_actual:
                        continue

                    # Filtrar estudiantes para este complemento específico
                    estudiantes_filtrados = [
                        est for est in estudiantes_sede
                        if nombre_amigable_actual in est.complementos_activos
                        est for est in estudiantes_sede if nombre_amigable_actual in est.complementos_activos
                    ]

                    # Construir datos del encabezado
                    datos_encabezado = PDFAsistenciaService.construir_datos_encabezado(
                        datos_geograficos, nombre_sede_focalizacion, dane_ie,
                        programa_obj, mes, ano, codigo
                    )
                    ruta_logo_final = None
                    if programa_obj and programa_obj.imagen:
                        ruta_logo_final = programa_obj.imagen.path

                    # Generar PDF
                    # Construir el nombre de la institución con la focalización
                    institucion_con_focalizacion = f"{focalizacion} {nombre_sede_focalizacion}"

                    datos_encabezado = {
                        'departamento': departamento_obj.nombre_departamento if departamento_obj else 'N/A',
                        'institucion': institucion_con_focalizacion,
                        'municipio': nombre_municipio_etc,
                        'dane_ie': dane_ie,
                        'operador': programa_obj.programa if programa_obj else 'N/A',
                        'contrato': programa_obj.contrato if programa_obj else 'N/A',
                        'mes': mes.upper(),
                        'ano': str(ano),
                        'dane_departamento': dane_departamento,
                        'dane_municipio': dane_municipio,
                        'codigo_complemento': codigo,
                        'ruta_logo': ruta_logo_final
                    }

                    pdf_buffer = BytesIO()
                    crear_formato_asistencia(pdf_buffer, datos_encabezado, estudiantes_filtrados)

                    # Agregar PDF al ZIP
                    nombre_archivo_pdf = f"Asistencia_{sede_obj.nombre_sede_educativa.replace(' ', '_')}_{codigo}_{mes}_{str(ano)}.pdf"
                    
                    nombre_archivo_pdf = f"Asistencia_{sede_obj.nombre_sede_educativa.replace(' ', '_')}_{codigo}_{mes}_{ano}.pdf"
                    zip_file.writestr(nombre_archivo_pdf, pdf_buffer.getvalue())

            # Preparar respuesta
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer, content_type='application/zip')
            nombre_archivo_zip = f"Asistencias_{sede_obj.nombre_sede_educativa.replace(' ', '_').replace('/', '_')}_{str(focalizacion)}_{str(mes)}.zip"
            response['Content-Disposition'] = f'attachment; filename="{nombre_archivo_zip}"'
            response['Content-Disposition'] = f'attachment; filename="Asistencias_{sede_obj.nombre_sede_educativa.replace(" ", "_")}_{focalizacion}_{mes}.zip"'
            return response

        except Exception as e:
            FacturacionLogger.log_procesamiento_error(f"generar_pdf_asistencia_{sede_cod_interprise}", str(e))
            return HttpResponse(f"Error al generar el PDF: {e}", status=500)