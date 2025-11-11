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

    def generar_pdf_asistencia(programa_id, sede_cod_interprise, mes, focalizacion, dias_personalizados=None):

        """

        Lógica de negocio para generar los PDFs de asistencia para una sede, mes y focalización, basado en un programa.

        """

        try:

            programa_obj = get_object_or_404(Programa, id=programa_id)

            sede_obj = get_object_or_404(SedesEducativas.objects.select_related(

                'codigo_ie__id_municipios'

            ), cod_interprise=sede_cod_interprise)



            estudiantes_sede = ListadosFocalizacion.objects.filter(

                programa=programa_obj,

                sede=sede_obj.nombre_sede_educativa,

                focalizacion=focalizacion

            ).order_by('apellido1', 'apellido2', 'nombre1')



            def clave_ordenamiento_grado(estudiante):

                grado_base_str = _extraer_grado_base(estudiante.grado_grupos)

                try:

                    return int(grado_base_str)

                except (ValueError, TypeError):

                    return float('inf')



            estudiantes_sede_sorted = sorted(list(estudiantes_sede), key=clave_ordenamiento_grado)



            if not estudiantes_sede_sorted:

                return HttpResponse(f"No se encontraron estudiantes para la sede {sede_obj.nombre_sede_educativa} en el programa {programa_obj.programa} con la focalización '{focalizacion}'.", status=404)



            return PDFAsistenciaService._generar_zip_para_sede(estudiantes_sede_sorted, sede_obj, mes, focalizacion, programa_obj, dias_personalizados=dias_personalizados)



        except Exception as e:

            return HttpResponse(f"Error al generar el PDF: {e}", status=500)



    @staticmethod

    def generar_zip_masivo_por_programa(programa_id, mes, focalizacion, dias_personalizados=None):

        """

        Genera un ZIP masivo con todos los PDFs de asistencia para todas las sedes de un Programa.

        """

        try:

            programa_obj = get_object_or_404(Programa, id=programa_id)



            # Obtener todas las sedes que tienen estudiantes para este programa y focalización

            sedes_con_registros_nombres = ListadosFocalizacion.objects.filter(

                programa=programa_obj,

                focalizacion=focalizacion

            ).values_list('sede', flat=True).distinct()



            sedes_del_programa = SedesEducativas.objects.filter(

                nombre_sede_educativa__in=sedes_con_registros_nombres

            ).select_related('codigo_ie__id_municipios').order_by('nombre_sede_educativa')



            if not sedes_del_programa.exists():

                return HttpResponse(f"No se encontraron sedes con estudiantes para el programa '{programa_obj.programa}' y la focalización '{focalizacion}'.", status=404)



            zip_buffer = BytesIO()

            sedes_procesadas = 0

            

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, False) as zip_file_principal:

                

                for sede_obj in sedes_del_programa:

                    estudiantes_sede = ListadosFocalizacion.objects.filter(

                        programa=programa_obj,

                        sede=sede_obj.nombre_sede_educativa,

                        focalizacion=focalizacion

                    ).order_by('apellido1', 'apellido2', 'nombre1')



                    if not estudiantes_sede.exists():

                        continue



                    def clave_ordenamiento_grado(estudiante):

                        grado_base_str = _extraer_grado_base(estudiante.grado_grupos)

                        try:

                            return int(grado_base_str)

                        except (ValueError, TypeError):

                            return float('inf')



                    estudiantes_sede_sorted = sorted(list(estudiantes_sede), key=clave_ordenamiento_grado)



                    zip_sede_buffer = PDFAsistenciaService._crear_zip_interno_para_sede(

                        estudiantes_sede_sorted, sede_obj, mes, focalizacion, programa_obj, dias_personalizados=dias_personalizados

                    )

                    

                    if zip_sede_buffer:

                        nombre_carpeta_sede = f"{sede_obj.nombre_sede_educativa.replace(' ', '_').replace('/', '_')}"

                        

                        with zipfile.ZipFile(zip_sede_buffer, 'r') as zip_sede:

                            for nombre_archivo in zip_sede.namelist():

                                contenido_pdf = zip_sede.read(nombre_archivo)

                                ruta_en_zip_principal = f"{nombre_carpeta_sede}/{nombre_archivo}"

                                zip_file_principal.writestr(ruta_en_zip_principal, contenido_pdf)

                        

                        sedes_procesadas += 1



            if sedes_procesadas == 0:

                return HttpResponse(f"No se generaron reportes. Verifique que las sedes tengan estudiantes con complementos asignados para la focalización '{focalizacion}'.", status=404)



            zip_buffer.seek(0)

            response = HttpResponse(zip_buffer, content_type='application/zip')

            nombre_archivo_zip = f"Asistencias_Masivo_{programa_obj.programa.replace(' ', '_')}_{focalizacion.replace(' ', '_')}_{mes}.zip"

            response['Content-Disposition'] = f'attachment; filename="{nombre_archivo_zip}"'

            return response



        except Exception as e:

            return HttpResponse(f"Error al generar el ZIP masivo: {e}", status=500)



    @staticmethod

    def _generar_zip_para_sede(estudiantes_sede, sede_obj, mes, focalizacion, programa_obj, dias_personalizados=None):

        """

        Método auxiliar para generar el ZIP de una sede específica (para respuesta HTTP).

        """

        zip_buffer = PDFAsistenciaService._crear_zip_interno_para_sede(

            estudiantes_sede, sede_obj, mes, focalizacion, programa_obj, dias_personalizados=dias_personalizados

        )



        if not zip_buffer:

            return HttpResponse("No hay estudiantes con complementos asignados en esta sede.", status=404)



        zip_buffer.seek(0)

        response = HttpResponse(zip_buffer, content_type='application/zip')

        nombre_archivo_zip = f"Asistencias_{sede_obj.nombre_sede_educativa.replace(' ', '_').replace('/', '_')}_{str(focalizacion)}_{str(mes)}.zip"

        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo_zip}"'

        return response



    @staticmethod

    def _crear_zip_interno_para_sede(estudiantes_sede, sede_obj, mes, focalizacion, programa_obj, dias_personalizados=None):

        """

        Método auxiliar para crear un ZIP interno de una sede (para uso en ZIP masivo).

        Retorna un BytesIO buffer con el ZIP generado.

        """

        if not estudiantes_sede:

            return None



        nombre_municipio_etc = programa_obj.municipio.nombre_municipio

        dane_municipio = programa_obj.municipio.codigo_municipio

        

        try:

            departamento_obj = PrincipalDepartamento.objects.get(codigo_departamento=programa_obj.municipio.codigo_departamento)

            dane_departamento = departamento_obj.codigo_departamento

        except PrincipalDepartamento.DoesNotExist:

            departamento_obj = None

            dane_departamento = 'N/A'



        nombre_sede_focalizacion = sede_obj.nombre_sede_educativa

        es_industrializado = False

        try:

            sede_info_dane = SedesEducativas.objects.get(nombre_sede_educativa=nombre_sede_focalizacion)

            dane_ie = sede_info_dane.cod_dane

            es_industrializado = sede_info_dane.industrializado == 'VERDADERO'

        except SedesEducativas.DoesNotExist:

            dane_ie = 'DANE no encontrado'



        ano = estudiantes_sede[0].ano

        if not ano:

            return None



        if es_industrializado:

            mapeo_codigos = {

                "CAP AM": "CAJMRI",

                "CAP PM": "CAJTRI",

                "Almuerzo JU": "ALMUERZO",

                "Refuerzo": "RCRI"

            }

        else:

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



                institucion_con_focalizacion = f"{focalizacion} {nombre_sede_focalizacion}"



                datos_encabezado = {

                    'departamento': str(departamento_obj.nombre_departamento),

                    'institucion': str(institucion_con_focalizacion),

                    'municipio': str(nombre_municipio_etc),

                    'dane_ie': str(dane_ie),

                    'operador': str(programa_obj.programa),

                    'contrato': str(programa_obj.contrato),

                    'mes': str(mes).upper(),

                    'ano': str(ano),

                    'dane_departamento': str(dane_departamento),

                    'dane_municipio': str(dane_municipio),

                    'codigo_complemento': str(codigo),

                    'ruta_logo': ruta_logo_final,

                    'dias_personalizados': dias_personalizados

                }



                pdf_buffer = BytesIO()

                crear_formato_asistencia(pdf_buffer, datos_encabezado, estudiantes_filtrados)

                

                nombre_archivo_pdf = f"Asistencia_{sede_obj.nombre_sede_educativa.replace(' ', '_')}_{str(codigo)}_{str(mes)}_{str(ano)}.pdf"

                zip_file.writestr(nombre_archivo_pdf, pdf_buffer.getvalue())



        zip_buffer.seek(0)

        return zip_buffer
