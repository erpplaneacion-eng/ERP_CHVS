from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from ..master_excel_generator import MasterNutritionalExcelGenerator
from ..excel_generator import generate_advanced_nutritional_excel, generate_excel_from_service
from ..guia_preparacion_excel_generator import GuiaPreparacionExcelGenerator
from ..services import AnalisisNutricionalService


@login_required
def download_menu_excel(request, menu_id):
    """
    View to download an Excel file for a specific menu with advanced data integration.
    """
    try:
        excel_stream = generate_advanced_nutritional_excel(menu_id, use_saved_analysis=True)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_id}_analisis_nutricional.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando Excel: {str(e)}", status=500)


@login_required
def download_menu_excel_service(request, menu_id):
    """
    View to download an Excel file using the nutritional analysis service directly.
    """
    try:
        excel_stream = generate_excel_from_service(menu_id)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_id}_servicio_analisis.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando Excel desde servicio: {str(e)}", status=500)


@login_required
def download_menu_excel_with_nivel(request, menu_id, nivel_escolar_id):
    """
    View to download an Excel file for a specific menu and school level with advanced data integration.
    """
    try:
        excel_stream = generate_advanced_nutritional_excel(menu_id, nivel_escolar_id, use_saved_analysis=True)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_id}_nivel_{nivel_escolar_id}_analisis.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando Excel: {str(e)}", status=500)


@login_required
def download_modalidad_excel(request, programa_id, modalidad_id):
    """
    Descarga el reporte maestro de Excel para todos los menús de una modalidad.
    """
    try:
        masive_data = AnalisisNutricionalService.obtener_analisis_masivo_por_modalidad(
            programa_id=programa_id,
            modalidad_id=modalidad_id
        )

        if not masive_data.get('success'):
            raise ValueError("No se pudieron generar los datos para el reporte maestro.")

        generator = MasterNutritionalExcelGenerator()
        excel_stream = generator.generate(masive_data)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"reporte_maestro_{masive_data['programa_nombre']}_{masive_data['modalidad_nombre']}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando el reporte maestro de Excel: {str(e)}", status=500)


@login_required
def download_guias_preparacion_excel(request, programa_id, modalidad_id):
    """
    Descarga archivo de guias de preparacion:
    una hoja por menu para el programa/modalidad seleccionados.
    """
    try:
        generator = GuiaPreparacionExcelGenerator()
        excel_stream = generator.generate(programa_id=programa_id, modalidad_id=modalidad_id)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="guias_preparacion_programa_{programa_id}_modalidad_{modalidad_id}.xlsx"'
        )
        return response
    except Exception as e:
        return HttpResponse(f"Error generando guias de preparacion: {str(e)}", status=500)
