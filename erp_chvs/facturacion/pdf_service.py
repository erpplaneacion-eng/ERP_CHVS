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

            # --- INICIO DE CAMBIO SOLICITADO ---
            # Ordenar la lista de estudiantes por grado educativo de forma ascendente
            def clave_ordenamiento_grado(estudiante):
                grado_base_str = _extraer_grado_base(estudiante.grado_grupos)
                try:
                    # Convertir a entero para un ordenamiento numérico correcto
                    return int(grado_base_str)
                except (ValueError, TypeError):
                    # Si no se puede convertir, se le da un valor alto para que vaya al final
                    return float('inf')

            estudiantes_sede = sorted(list(estudiantes_sede), key=clave_ordenamiento_grado)
            # --- FIN DE CAMBIO SOLICITADO ---

            if not estudiantes_sede:
                return HttpResponse(f"No se encontraron estudiantes para la sede {sede_obj.nombre_sede_educativa} con la focalización '{focalizacion}'.", status=404)

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
            try:
                sede_info_dane = SedesEducativas.objects.get(nombre_sede_educativa=nombre_sede_focalizacion)
                dane_ie = sede_info_dane.cod_dane
            except SedesEducativas.DoesNotExist:
                dane_ie = 'DANE no encontrado'

            ano = primer_estudiante.ano
            if not ano:
                return HttpResponse(f"No se pudo determinar el año para la focalización '{focalizacion}'.", status=404)

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

        except Exception as e:
            return HttpResponse(f"Error al generar el PDF: {e}", status=500)