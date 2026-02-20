import os
import django
import sys

# Configurar entorno Django
sys.path.append('erp_chvs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.services.analisis_service import AnalisisNutricionalService

def simular_excel_detallado():
    id_menu = 664
    try:
        data = AnalisisNutricionalService.obtener_analisis_completo(id_menu)
        if not data.get('success'): return

        # Tomar nivel prescolar
        nivel_data = data.get('analisis_por_nivel', [])[0]
        
        # Encabezados del Excel (las 14 columnas)
        headers = [
            "COMPONENTE", "GRUPO", "PREPARACIÓN", "ALIMENTO", "CÓDIGO", 
            "P.BRUTO", "P.NETO", "KCAL", "PROT", "GRASA", "CHO", "CALCIO", "HIERRO", "SODIO"
        ]
        
        print("| " + " | ".join([f"{h:<12}" for h in headers]) + " |")
        print("-" * 210)
        
        for prep in nivel_data.get('preparaciones', []):
            comp = prep.get('componente', 'N/A')
            grupo = prep.get('grupo_alimentos', 'N/A')
            prep_n = prep.get('nombre', 'N/A')
            
            for ing in prep.get('ingredientes', []):
                alimento = ing.get('nombre', 'N/A')[:12]
                codigo = ing.get('codigo_icbf', 'N/A')
                p_neto = float(ing.get('peso_neto_base', 0))
                p_bruto = float(ing.get('peso_bruto_base', 0))
                
                # Obtener nutrientes (usamos valores finales si existen, sino calculamos)
                val = ing.get('valores_finales_guardados', {})
                if not val:
                    v100 = ing.get('valores_por_100g', {})
                    val = {
                        'calorias': (v100.get('calorias_kcal', 0) * p_neto) / 100,
                        'proteina': (v100.get('proteina_g', 0) * p_neto) / 100,
                        'grasa': (v100.get('grasa_g', 0) * p_neto) / 100,
                        'cho': (v100.get('cho_g', 0) * p_neto) / 100,
                        'calcio': (v100.get('calcio_mg', 0) * p_neto) / 100,
                        'hierro': (v100.get('hierro_mg', 0) * p_neto) / 100,
                        'sodio': (v100.get('sodio_mg', 0) * p_neto) / 100,
                    }

                row = [
                    comp[:12], grupo[:12], prep_n[:12], alimento, str(codigo),
                    f"{p_bruto:.1f}", f"{p_neto:.1f}", f"{float(val['calorias']):.2f}", 
                    f"{float(val['proteina']):.2f}", f"{float(val['grasa']):.2f}", 
                    f"{float(val['cho']):.2f}", f"{float(val['calcio']):.2f}", 
                    f"{float(val['hierro']):.2f}", f"{float(val['sodio']):.2f}"
                ]
                print("| " + " | ".join([f"{str(item):<12}" for item in row]) + " |")

        # Totales
        print("-" * 210)
        t = nivel_data.get('totales', {})
        total_row = [
            "TOTALES", "", "", "", "", 
            f"{float(t.get('peso_bruto', 0)):.1f}", f"{float(t.get('peso_neto', 0)):.1f}",
            f"{float(t.get('calorias', 0)):.2f}", f"{float(t.get('proteina', 0)):.2f}",
            f"{float(t.get('grasa', 0)):.2f}", f"{float(t.get('cho', 0)):.2f}",
            f"{float(t.get('calcio', 0)):.2f}", f"{float(t.get('hierro', 0)):.2f}",
            f"{float(t.get('sodio', 0)):.2f}"
        ]
        print("| " + " | ".join([f"{str(item):<12}" for item in total_row]) + " |")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simular_excel_detallado()
