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
import logging

logger = logging.getLogger(__name__)

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

            # PRE-CARGAR EL LOGO UNA SOLA VEZ para evitar múltiples descargas desde Cloudinary
            # Esto es crítico en generación masiva para evitar timeouts
            logger.info("="*70)
            logger.info("🚀 INICIO GENERACIÓN ZIP MASIVO")
            logger.info(f"   Programa: {programa_obj.programa}")
            logger.info(f"   Focalización: {focalizacion}")
            logger.info(f"   Mes: {mes}")

            ruta_logo_precargado = None
            if programa_obj and programa_obj.imagen:
                from django.conf import settings
                from .pdf_generator import _logo_cache
                import requests
                from io import BytesIO
                from reportlab.lib.utils import ImageReader

                logger.info("📸 Iniciando pre-carga del logo del programa...")

                # Determinar la URL del logo
                if hasattr(settings, 'DEBUG') and not settings.DEBUG:
                    # Producción: usar URL de Cloudinary
                    logo_url = programa_obj.imagen.url
                    logger.info(f"   Entorno: PRODUCCIÓN (Cloudinary)")
                else:
                    # Desarrollo: intentar path local primero
                    try:
                        logo_url = programa_obj.imagen.path
                        logger.info(f"   Entorno: DESARROLLO (FileSystem)")
                    except (AttributeError, ValueError):
                        logo_url = programa_obj.imagen.url
                        logger.info(f"   Entorno: DESARROLLO (URL)")

                logger.info(f"   URL del logo: {logo_url[:80]}...")

                # Si es URL remota (Cloudinary), descargarla UNA VEZ y cachearla
                if isinstance(logo_url, str) and logo_url.startswith(("http://", "https://")):
                    if logo_url not in _logo_cache:
                        logger.info("   ⏳ Logo NO está en cache, descargando desde Cloudinary...")
                        try:
                            # Descargar con timeout generoso y reintentos
                            for intento in range(3):
                                try:
                                    logger.info(f"      Intento {intento + 1}/3 de descarga...")
                                    response = requests.get(logo_url, timeout=30, stream=True)
                                    response.raise_for_status()

                                    # Los logos ya vienen pre-optimizados (B/N, 400px, ~50KB)
                                    # gracias al método save() del modelo Programa
                                    image_content = BytesIO(response.content)
                                    logo_reader = ImageReader(image_content)
                                    _logo_cache[logo_url] = logo_reader
                                    ruta_logo_precargado = logo_url

                                    size_kb = len(response.content) / 1024
                                    logger.info(f"   ✅ Logo descargado exitosamente ({size_kb:.2f} KB)")
                                    logger.info(f"   💾 Logo guardado en cache global")
                                    logger.info(f"   📦 Cache contiene {len(_logo_cache)} entrada(s)")
                                    break
                                except requests.exceptions.Timeout as e:
                                    logger.warning(f"      ⚠️ Timeout en intento {intento + 1}: {e}")
                                    if intento < 2:
                                        continue
                                    else:
                                        logger.error("   ❌ Falló descarga después de 3 intentos (Timeout)")
                                except requests.exceptions.RequestException as e:
                                    logger.warning(f"      ⚠️ Error de red en intento {intento + 1}: {e}")
                                    if intento < 2:
                                        continue
                                    else:
                                        logger.error("   ❌ Falló descarga después de 3 intentos (RequestException)")
                        except Exception as e:
                            logger.error(f"   ❌ Error inesperado descargando logo: {e}")
                    else:
                        # Ya está en cache
                        ruta_logo_precargado = logo_url
                        logger.info("   ✅ Logo YA está en cache (reutilizando)")
                        logger.info(f"   📦 Cache contiene {len(_logo_cache)} entrada(s)")
                else:
                    # Es ruta local
                    ruta_logo_precargado = logo_url
                    logger.info(f"   ✅ Logo local listo: {logo_url}")
            else:
                logger.warning("   ⚠️ Programa sin imagen asignada, PDFs se generarán sin logo")

            logger.info("="*70)

            # Obtener todas las sedes que tienen estudiantes para este programa y focalización

            sedes_con_registros_nombres = ListadosFocalizacion.objects.filter(

                programa=programa_obj,

                focalizacion=focalizacion

            ).values_list('sede', flat=True).distinct()



            sedes_del_programa = SedesEducativas.objects.filter(

                nombre_sede_educativa__in=sedes_con_registros_nombres

            ).select_related('codigo_ie__id_municipios').order_by('nombre_generico_sede')



            if not sedes_del_programa.exists():

                return HttpResponse(f"No se encontraron sedes con estudiantes para el programa '{programa_obj.programa}' y la focalización '{focalizacion}'.", status=404)



            zip_buffer = BytesIO()

            sedes_procesadas = 0

            

            logger.info(f"\n📂 Procesando {sedes_del_programa.count()} sede(s)...\n")

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, False) as zip_file_principal:



                for sede_obj in sedes_del_programa:

                    logger.info(f"📍 Procesando sede: {sede_obj.nombre_sede_educativa}")

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

                    logger.info(f"   👥 {len(estudiantes_sede_sorted)} estudiante(s) encontrado(s)")


                    zip_sede_buffer = PDFAsistenciaService._crear_zip_interno_para_sede(

                        estudiantes_sede_sorted, sede_obj, mes, focalizacion, programa_obj, dias_personalizados=dias_personalizados

                    )



                    if zip_sede_buffer:

                        with zipfile.ZipFile(zip_sede_buffer, 'r') as zip_sede:
                            num_pdfs = len(zip_sede.namelist())
                            logger.info(f"   📄 {num_pdfs} PDF(s) generado(s) para esta sede")

                            for nombre_archivo in zip_sede.namelist():

                                contenido_pdf = zip_sede.read(nombre_archivo)

                                zip_file_principal.writestr(nombre_archivo, contenido_pdf)



                        sedes_procesadas += 1
                        logger.info(f"   ✅ Sede procesada exitosamente ({sedes_procesadas}/{sedes_del_programa.count()})\n")



            if sedes_procesadas == 0:
                logger.warning("⚠️ No se generaron reportes (sin sedes con estudiantes)")
                return HttpResponse(f"No se generaron reportes. Verifique que las sedes tengan estudiantes con complementos asignados para la focalización '{focalizacion}'.", status=404)

            # Definir nombre del archivo antes del logging
            nombre_archivo_zip = f"Asistencias_Masivo_{programa_obj.programa.replace(' ', '_')}_{focalizacion.replace(' ', '_')}_{mes}.zip"

            logger.info("="*70)
            logger.info("✅ GENERACIÓN ZIP MASIVO COMPLETADA")
            logger.info(f"   Sedes procesadas: {sedes_procesadas}")
            logger.info(f"   Archivo: {nombre_archivo_zip}")
            logger.info(f"   Tamaño: {zip_buffer.tell() / (1024*1024):.2f} MB")
            logger.info("="*70)

            zip_buffer.seek(0)

            response = HttpResponse(zip_buffer, content_type='application/zip')

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

        total_raciones_zip = len(estudiantes_sede)
        nombre_sede_limpio = sede_obj.nombre_generico_sede.replace(' ', '_').replace('/', '_')
        nombre_archivo_zip = f"Asistencias_{nombre_sede_limpio}_{str(focalizacion)}_{str(mes)}_{total_raciones_zip}raciones.zip"

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



        nombre_sede_focalizacion = sede_obj.nombre_generico_sede

        dane_ie = sede_obj.cod_dane
        es_industrializado = sede_obj.industrializado == 'VERDADERO'



        # Usar siempre el año actual para los reportes de asistencia
        from datetime import datetime
        ano = datetime.now().year



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



                # IMPORTANTE: En generación masiva, el logo ya fue pre-cargado en cache
                # por generar_zip_masivo_por_programa(), así que _resolver_fuente_logo()
                # lo encontrará en cache sin necesidad de descargarlo nuevamente
                ruta_logo_final = None

                if programa_obj and programa_obj.imagen:
                    from django.conf import settings
                    # En producción (Cloudinary), usar siempre .url
                    # En desarrollo (FileSystemStorage), usar .path si existe
                    if hasattr(settings, 'DEBUG') and not settings.DEBUG:
                        # Producción: usar URL de Cloudinary directamente
                        ruta_logo_final = programa_obj.imagen.url
                    else:
                        # Desarrollo: intentar ruta local primero
                        try:
                            ruta_logo_final = programa_obj.imagen.path
                        except (AttributeError, ValueError):
                            # Si falla .path, usar .url (puede ser relativa)
                            ruta_logo_final = programa_obj.imagen.url



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

                

                total_raciones_pdf = len(estudiantes_filtrados)
                nombre_sede_limpio_pdf = sede_obj.nombre_generico_sede.replace(' ', '_').replace('/', '_')
                nombre_archivo_pdf = f"Asistencia_{nombre_sede_limpio_pdf}_{str(codigo)}_{str(mes)}_{str(ano)}_{total_raciones_pdf}raciones.pdf"

                zip_file.writestr(nombre_archivo_pdf, pdf_buffer.getvalue())



        zip_buffer.seek(0)

        return zip_buffer
