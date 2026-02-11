import os
import sys
import django

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.services.analisis_service import AnalisisNutricionalService
from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo

def test_analisis_masivo():
    """
    Prueba la consolidación masiva de análisis nutricionales.
    """
    print("=" * 80)
    print("📊 PRUEBA DE ANÁLISIS NUTRICIONAL MASIVO POR MODALIDAD")
    print("=" * 80)

    # 1. Parámetros de prueba
    programa_id = 1 # TEST PROGRAM
    modalidad_id = 'mod1' # COMPLEMENTO ALIMENTARIO PREPARADO AM

    try:
        # 2. Ejecutar servicio masivo
        print(f"🔍 Procesando consolidación para Programa ID: {programa_id}, Modalidad ID: {modalidad_id}...")
        resultado = AnalisisNutricionalService.obtener_analisis_masivo_por_modalidad(programa_id, modalidad_id)

        if not resultado.get('success'):
            print("❌ El servicio devolvió un error.")
            return

        # 3. Mostrar Resumen General
        print("\n✅ CONSOLIDACIÓN EXITOSA")
        print(f"   • Programa: {resultado['programa_nombre']}")
        print(f"   • Modalidad: {resultado['modalidad_nombre']}")
        print(f"   • Niveles encontrados: {len(resultado['analisis_por_nivel'])}")
        print("-" * 80)

        # 4. Detalle por Nivel
        for nivel, menus_analisis in resultado['analisis_por_nivel'].items():
            print(f"\n📍 NIVEL: {nivel}")
            print(f"   {len(menus_analisis)} menús encontrados con análisis.")
            print("   " + "─" * 70)
            
            # Encabezado de tabla simple
            print(f"   {'Menú':<30} | {'Energía':<10} | {'Proteína':<10} | {'% Adecuac.'}")
            print("   " + "─" * 70)

            for item in menus_analisis:
                menu_info = item['menu_info']
                analisis = item['analisis']
                
                totales = analisis.get('totales', {})
                porcentajes = analisis.get('porcentajes_adecuacion', {})
                
                cal = totales.get('calorias', 0)
                prot = totales.get('proteina', 0)
                adeq_cal_dict = porcentajes.get('calorias', {})
                adeq_cal = adeq_cal_dict.get('porcentaje', 0)

                print(f"   {menu_info['nombre'][:30]:<30} | {cal:<10.1f} | {prot:<10.1f} | {adeq_cal:>5.1f}%")

        print("\n" + "=" * 80)
        print("✅ PRUEBA DE ANÁLISIS MASIVO COMPLETADA")
        print("=" * 80)

    except Exception as e:
        print(f"\n💥 ERROR DURANTE LA PRUEBA:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analisis_masivo()
