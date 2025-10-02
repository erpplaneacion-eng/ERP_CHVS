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
from .utils import _extraer_grado_base # Importar la función de ayuda

class PDFAsistenciaService:
    @staticmethod
    def generar_pdf_asistencia(sede_cod_interprise, mes, focalizacion):
        """
        Lógica de negocio para generar los PDFs de asistencia para una sede, mes y focalización.
        Crea un archivo ZIP con un PDF por cada tipo de complemento.
        """
        try:
            sede_obj = get_object_or_404(SedesEducativas.objects.select_related(
                'codigo_ie__id_municipios'
            ), cod_interprise=sede_cod_interprise)

            estudiantes_sede = ListadosFocalizacion.objects.filter(
                sede=sede_obj.nombre_sede_educativa,
                focalizacion=focalizacion
            ).order_by('apellido1', 'apellido2', 'nombre1')

            # Ordenar la lista de estudiantes por grado educativo de forma ascendente
            def clave_ordenamiento_grado(estudiante):
                grado_base_str = _extraer_grado_base(estudiante.grado_grupos)
                try:
                    return int(grado_base_str)
                except (ValueError, TypeError):
                    return float('inf')

            estudiantes_sede = sorted(list(estudiantes_sede), key=clave_ordenamiento_grado)

            if not estudiantes_sede:
                return HttpResponse(f"No se encontraron estudiantes para la sede {sede_obj.nombre_sede_educativa} con la focalización '{focalizacion}'.", status=404)

            return PDFAsistenciaService._generar_zip_para_sede(estudiantes_sede, sede_obj, mes, focalizacion)

        except Exception as e:
            return HttpResponse(f"Error al generar el PDF: {e}", status=500)

    @staticmethod
    def generar_zip_masivo_por_etc(etc, mes, focalizacion):
        """
        Genera un ZIP masivo con todos los PDFs de asistencia para todas las sedes de un ETC.
        
        Args:
            etc: Nombre del municipio/ETC
            mes: Mes de atención
            focalizacion: Tipo de focalización
        
        Returns:
            HttpResponse: Archivo ZIP con todos los PDFs de las sedes del ETC
        """
        try:
            # Obtener todas las sedes del ETC
            sedes_etc = SedesEducativas.objects.filter(
                codigo_ie__id_municipios__nombre_municipio__icontains=etc
            ).select_related('codigo_ie__id_municipios').order_by('nombre_sede_educativa')

            if not sedes_etc.exists():
                return HttpResponse(f"No se encontraron sedes para el ETC '{etc}'.", status=404)

            # Verificar que existan estudiantes con esa focalización en el ETC
            estudiantes_etc = ListadosFocalizacion.objects.filter(
                etc__icontains=etc,
                focalizacion=focalizacion
            )

            if not estudiantes_etc.exists():
                return HttpResponse(f"No se encontraron estudiantes para el ETC '{etc}' con la focalización '{focalizacion}'.", status=404)

            zip_buffer = BytesIO()
            sedes_procesadas = 0
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, False) as zip_file_principal:
                
                for sede_obj in sedes_etc:
                    # Filtrar estudiantes por sede específica
                    estudiantes_sede = ListadosFocalizacion.objects.filter(
                        sede=sede_obj.nombre_sede_educativa,
                        focalizacion=focalizacion
                    ).order_by('apellido1', 'apellido2', 'nombre1')

                    if not estudiantes_sede.exists():
                        continue  # Saltar sedes sin estudiantes

                    # Ordenar por grado educativo
                    def clave_ordenamiento_grado(estudiante):
                        grado_base_str = _extraer_grado_base(estudiante.grado_grupos)
                        try:
                            return int(grado_base_str)
                        except (ValueError, TypeError):
                            return float('inf')

                    estudiantes_sede = sorted(list(estudiantes_sede), key=clave_ordenamiento_grado)

                    # Generar ZIP para esta sede y agregarlo al ZIP principal
                    zip_sede_buffer = PDFAsistenciaService._crear_zip_interno_para_sede(
                        estudiantes_sede, sede_obj, mes, focalizacion
                    )
                    
                    if zip_sede_buffer:
                        # Crear nombre de carpeta para la sede
                        nombre_carpeta_sede = f"{sede_obj.nombre_sede_educativa.replace(' ', '_').replace('/', '_')}"
                        
                        # Extraer los PDFs del ZIP de la sede y agregarlos con estructura de carpetas
                        with zipfile.ZipFile(zip_sede_buffer, 'r') as zip_sede:
                            for nombre_archivo in zip_sede.namelist():
                                contenido_pdf = zip_sede.read(nombre_archivo)
                                ruta_en_zip_principal = f"{nombre_carpeta_sede}/{nombre_archivo}"
                                zip_file_principal.writestr(ruta_en_zip_principal, contenido_pdf)
                        
                        sedes_procesadas += 1

            if sedes_procesadas == 0:
                return HttpResponse(f"No se encontraron sedes con estudiantes para el ETC '{etc}' y focalización '{focalizacion}'.", status=404)

            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer, content_type='application/zip')
            nombre_archivo_zip = f"Asistencias_Masivo_{etc.replace(' ', '_')}_{focalizacion.replace(' ', '_')}_{mes}.zip"
            response['Content-Disposition'] = f'attachment; filename="{nombre_archivo_zip}"'
            return response

        except Exception as e:
            return HttpResponse(f"Error al generar el ZIP masivo: {e}", status=500)

    @staticmethod
    def _generar_zip_para_sede(estudiantes_sede, sede_obj, mes, focalizacion):
        """
        Método auxiliar para generar el ZIP de una sede específica (para respuesta HTTP).
        """
        primer_estudiante = estudiantes_sede[0]
        nombre_municipio_etc = primer_estudiante.etc

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
        es_industrializado = False
        try:
            sede_info_dane = SedesEducativas.objects.get(nombre_sede_educativa=nombre_sede_focalizacion)
            dane_ie = sede_info_dane.cod_dane
            # Verificar si la sede es industrializada
            es_industrializado = sede_info_dane.industrializado == 'VERDADERO'
        except SedesEducativas.DoesNotExist:
            dane_ie = 'DANE no encontrado'

        ano = primer_estudiante.ano
        if not ano:
            return HttpResponse(f"No se pudo determinar el año para la focalización '{focalizacion}'.", status=404)

        # Mapeo de códigos según si es industrializado o no
        if es_industrializado:
            mapeo_codigos = {
                "CAP AM": "CAJMRI",    # Ración Industrializada
                "CAP PM": "CAJTRI",    # Ración Industrializada
                "Almuerzo JU": "ALMUERZO",  # Se mantiene igual
                "Refuerzo": "RRI"      # Ración Industrializada
            }
        else:
            mapeo_codigos = {
                "CAP AM": "CAJMPS",    # Preparado en Sitio
                "CAP PM": "CAJTPS",    # Preparado en Sitio
                "Almuerzo JU": "ALMUERZO",
                "Refuerzo": "RCPS"     # Preparado en Sitio
            }

        codigos_presentes = set()
        for est in estudiantes_sede:
            for comp_amigable in est.complementos_activos:
                if comp_amigable in mapeo_codigos:
                    codigos_presentes.add(mapeo_codigos[comp_amigable])

        if not codigos_presentes:
            return HttpResponse("No hay estudiantes con complementos asignados en esta sede.", status=404)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            for codigo in codigos_presentes:
                nombre_amigable_actual = next((key for key, value in mapeo_codigos.items() if value == codigo), None)
                if not nombre_amigable_actual:
                    continue

                estudiantes_filtrados = [
                    est for est in estudiantes_sede if nombre_amigable_actual in est.complementos_activos
                ]

                ruta_logo_final = None
                if programa_obj and programa_obj.imagen:
                    ruta_logo_final = programa_obj.imagen.path

                # Construir el nombre de la institución con la focalización
                institucion_con_focalizacion = f"{focalizacion} {nombre_sede_focalizacion}"

                datos_encabezado = {
                    'departamento': str(departamento_obj.nombre_departamento) if departamento_obj else 'N/A',
                    'institucion': str(institucion_con_focalizacion),
                    'municipio': str(nombre_municipio_etc),
                    'dane_ie': str(dane_ie),
                    'operador': str(programa_obj.programa) if programa_obj else 'N/A',
                    'contrato': str(programa_obj.contrato) if programa_obj else 'N/A',
                    'mes': str(mes).upper(),
                    'ano': str(ano),
                    'dane_departamento': str(dane_departamento),
                    'dane_municipio': str(dane_municipio),
                    'codigo_complemento': str(codigo),
                    'ruta_logo': ruta_logo_final
                }

                pdf_buffer = BytesIO()
                crear_formato_asistencia(pdf_buffer, datos_encabezado, estudiantes_filtrados)
                
                nombre_archivo_pdf = f"Asistencia_{sede_obj.nombre_sede_educativa.replace(' ', '_')}_{str(codigo)}_{str(mes)}_{str(ano)}.pdf"
                zip_file.writestr(nombre_archivo_pdf, pdf_buffer.getvalue())

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        nombre_archivo_zip = f"Asistencias_{sede_obj.nombre_sede_educativa.replace(' ', '_').replace('/', '_')}_{str(focalizacion)}_{str(mes)}.zip"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo_zip}"'
        return response

    @staticmethod
    def _crear_zip_interno_para_sede(estudiantes_sede, sede_obj, mes, focalizacion):
        """
        Método auxiliar para crear un ZIP interno de una sede (para uso en ZIP masivo).
        Retorna un BytesIO buffer con el ZIP generado.
        """
        if not estudiantes_sede:
            return None

        primer_estudiante = estudiantes_sede[0]
        nombre_municipio_etc = primer_estudiante.etc

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
        es_industrializado = False
        try:
            sede_info_dane = SedesEducativas.objects.get(nombre_sede_educativa=nombre_sede_focalizacion)
            dane_ie = sede_info_dane.cod_dane
            # Verificar si la sede es industrializada
            es_industrializado = sede_info_dane.industrializado == 'VERDADERO'
        except SedesEducativas.DoesNotExist:
            dane_ie = 'DANE no encontrado'

        ano = primer_estudiante.ano
        if not ano:
            return None

        # Mapeo de códigos según si es industrializado o no
        if es_industrializado:
            mapeo_codigos = {
                "CAP AM": "CAJMRI",    # Ración Industrializada
                "CAP PM": "CAJTRI",    # Ración Industrializada
                "Almuerzo JU": "ALMUERZO",  # Se mantiene igual
                "Refuerzo": "RRI"      # Ración Industrializada
            }
        else:
            mapeo_codigos = {
                "CAP AM": "CAJMPS",    # Preparado en Sitio
                "CAP PM": "CAJTPS",    # Preparado en Sitio
                "Almuerzo JU": "ALMUERZO",
                "Refuerzo": "RCPS"     # Preparado en Sitio
            }

        codigos_presentes = set()
        for est in estudiantes_sede:
            for comp_amigable in est.complementos_activos:
                if comp_amigable in mapeo_codigos:
                    codigos_presentes.add(mapeo_codigos[comp_amigable])

        if not codigos_presentes:
            return None

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, False) as zip_file:
            for codigo in codigos_presentes:
                nombre_amigable_actual = next((key for key, value in mapeo_codigos.items() if value == codigo), None)
                if not nombre_amigable_actual:
                    continue

                estudiantes_filtrados = [
                    est for est in estudiantes_sede if nombre_amigable_actual in est.complementos_activos
                ]

                ruta_logo_final = None
                if programa_obj and programa_obj.imagen:
                    ruta_logo_final = programa_obj.imagen.path

                # Construir el nombre de la institución con la focalización
                institucion_con_focalizacion = f"{focalizacion} {nombre_sede_focalizacion}"

                datos_encabezado = {
                    'departamento': str(departamento_obj.nombre_departamento) if departamento_obj else 'N/A',
                    'institucion': str(institucion_con_focalizacion),
                    'municipio': str(nombre_municipio_etc),
                    'dane_ie': str(dane_ie),
                    'operador': str(programa_obj.programa) if programa_obj else 'N/A',
                    'contrato': str(programa_obj.contrato) if programa_obj else 'N/A',
                    'mes': str(mes).upper(),
                    'ano': str(ano),
                    'dane_departamento': str(dane_departamento),
                    'dane_municipio': str(dane_municipio),
                    'codigo_complemento': str(codigo),
                    'ruta_logo': ruta_logo_final
                }

                pdf_buffer = BytesIO()
                crear_formato_asistencia(pdf_buffer, datos_encabezado, estudiantes_filtrados)
                
                nombre_archivo_pdf = f"Asistencia_{sede_obj.nombre_sede_educativa.replace(' ', '_')}_{str(codigo)}_{str(mes)}_{str(ano)}.pdf"
                zip_file.writestr(nombre_archivo_pdf, pdf_buffer.getvalue())

        zip_buffer.seek(0)
        return zip_buffer