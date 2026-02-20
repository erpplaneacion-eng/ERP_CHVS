import os
import django
import sys

# Configurar entorno Django
sys.path.append('erp_chvs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.services.analisis_service import AnalisisNutricionalService

def simular_excel_menu_1():
    id_menu = 664
    print(f"--- SIMULACIÓN EXCEL MENÚ 1 (ID: {id_menu}) MODALIDAD 20501 ---")
    
    try:
        data = AnalisisNutricionalService.obtener_analisis_completo(id_menu)
        
        if not data.get('success'):
            print("Error: No se pudo obtener el análisis.")
            return

        print(f"Menú: {data['menu']['nombre']}")
        print(f"Modalidad: {data['menu']['modalidad']}")
        print(f"Programa: {data['menu']['programa']}")
        print("-" * 110)
        
        # Tomar el primer nivel escolar para el análisis
        niveles = data.get('analisis_por_nivel', [])
        if not niveles:
            print("No se encontraron niveles escolares para este menú.")
            return
            
        nivel_data = niveles[0]
        print(f"Nivel Escolar: {nivel_data['nivel_escolar']['nombre']}")
        print(f"{'COMPONENTE':<20} | {'PREPARACIÓN':<25} | {'INGREDIENTE':<25} | {'P.NETO':<7} | {'CALORÍAS':<10} | {'PROT':<6}")
        print("-" * 110)
        
        for prep in nivel_data.get('preparaciones', []):
            comp = prep.get('componente', 'N/A')
            prep_nombre = prep.get('nombre', 'N/A')
            
            for ing in prep.get('ingredientes', []):
                ing_nombre = ing.get('nombre', 'N/A')[:25]
                p_neto = ing.get('peso_neto_base', 0)
                
                # Valores nutricionales finales (ya calculados por el servicio)
                valores = ing.get('valores_finales_guardados', {})
                if not valores:
                    # Si no hay guardados, calculamos sobre la marcha para la simulación
                    v100 = ing.get('valores_por_100g', {})
                    cal = (v100.get('calorias_kcal', 0) * float(p_neto)) / 100
                    prot = (v100.get('proteina_g', 0) * float(p_neto)) / 100
                else:
                    cal = valores.get('calorias', 0)
                    prot = valores.get('proteina', 0)
                
                print(f"{comp[:20]:<20} | {prep_nombre[:25]:<25} | {ing_nombre:<25} | {float(p_neto):<7.1f} | {float(cal):<10.2f} | {float(prot):<6.2f}")

        print("-" * 110)
        totales = nivel_data.get('totales', {})
        print(f"{'TOTALES':<75} | {float(totales.get('peso_neto', 0)):<7.1f} | {float(totales.get('calorias', 0)):<10.2f} | {float(totales.get('proteina', 0)):<6.2f}")
        
        pcts = nivel_data.get('porcentajes_adecuacion', {})
        
        # Extraer el valor numérico del porcentaje (que viene como dict {'adecuacion': X, ...})
        def get_pct_val(d):
            if isinstance(d, dict): return d.get('adecuacion', 0)
            return d

        cal_pct = get_pct_val(pcts.get('calorias', 0))
        prot_pct = get_pct_val(pcts.get('proteina', 0))

        print(f"{'% ADECUACIÓN':<75} | {'':<7} | {float(cal_pct):<10.1f}% | {float(prot_pct):<6.1f}%")
        print("-" * 110)
        
        # Verificación de Requerimientos
        reqs = nivel_data.get('requerimientos', {})
        print(f"{'REQUERIMIENTOS (Resolución)':<85} | {float(reqs.get('calorias', 0)):<10.2f} | {float(reqs.get('proteina', 0)):<6.2f}")

    except Exception as e:
        print(f"Error durante la simulación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simular_excel_menu_1()
