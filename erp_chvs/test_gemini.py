
import os
import sys
import django
import json

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.services.menu_service import MenuService
from nutricion.services.gemini_service import GeminiService
from nutricion.models import TablaMenus, TablaAnalisisNutricionalMenu, TablaIngredientesPorNivel
from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo, TablaGradosEscolaresUapa

def test_ia_generation_multinivel():
    """
    Prueba la generación de menús con IA para TODOS los niveles educativos.
    Valida que los pesos se guarden correctamente en TablaIngredientesPorNivel.
    """
    print("=" * 70)
    print("🚀 PRUEBA DE GENERACIÓN DE MENÚ CON GEMINI AI - MULTINIVEL")
    print("=" * 70)

    # 1. Obtener datos base
    programa = Programa.objects.first()
    if not programa:
        print("❌ No hay programas en la base de datos.")
        return

    # Usar el nombre exacto que espera el JSON de Minutas
    modalidad_nombre = "COMPLEMENTO ALIMENTARIO PREPARADO AM"
    modalidad, created = ModalidadesDeConsumo.objects.get_or_create(
        id_modalidades="mod1",
        defaults={"modalidad": modalidad_nombre}
    )

    # Obtener todos los niveles educativos
    niveles_db = list(TablaGradosEscolaresUapa.objects.values_list('nivel_escolar_uapa', flat=True))

    print(f"\n📋 CONFIGURACIÓN DE PRUEBA:")
    print(f"   • Programa: {programa.programa} (ID: {programa.id})")
    print(f"   • Modalidad: {modalidad.modalidad}")
    print(f"   • Niveles educativos en BD: {len(niveles_db)}")
    for nivel in niveles_db:
        print(f"     - {nivel}")
    print("-" * 70)

    try:
        # 2. Llamar a generación con IA
        print("\n🤖 LLAMANDO A GEMINI AI...")
        print("   (Esto puede tardar 10-30 segundos dependiendo de la API)")
        print("-" * 70)

        menu = MenuService.generar_menu_con_ia(
            id_programa=programa.id,
            id_modalidad=modalidad.id_modalidades,
            niveles_educativos=None  # None = usar todos los niveles
        )

        if not menu:
            print("❌ La IA no devolvió una propuesta válida.")
            return

        # 3. VALIDAR RESULTADOS
        print("\n✅ ¡MENÚ GENERADO EXITOSAMENTE!")
        print(f"   • Nombre: {menu.menu}")
        print(f"   • ID: {menu.id_menu}")
        print(f"   • Modalidad: {menu.id_modalidad.modalidad}")
        print("-" * 70)

        # 4. VALIDAR PREPARACIONES
        preparaciones = menu.preparaciones.all()
        print(f"\n📝 PREPARACIONES CREADAS: {preparaciones.count()}")
        for i, prep in enumerate(preparaciones, 1):
            componente = prep.id_componente.componente if prep.id_componente else 'Sin componente'
            print(f"   {i}. {prep.preparacion} [{componente}]")

            # Ingredientes base (sin peso)
            ingredientes_base = prep.ingredientes.all()
            print(f"      • Ingredientes base: {ingredientes_base.count()}")
        print("-" * 70)

        # 5. VALIDAR ANÁLISIS NUTRICIONAL POR NIVEL
        analisis_nutricionales = TablaAnalisisNutricionalMenu.objects.filter(id_menu=menu)
        print(f"\n🎯 ANÁLISIS NUTRICIONAL POR NIVEL: {analisis_nutricionales.count()}")

        if analisis_nutricionales.count() == 0:
            print("   ⚠️  WARNING: No se crearon análisis nutricionales")
            return

        for analisis in analisis_nutricionales:
            nivel = analisis.id_nivel_escolar_uapa.nivel_escolar_uapa
            print(f"\n   📊 NIVEL: {nivel}")
            print(f"   " + "─" * 60)

            # 6. VALIDAR PESOS GUARDADOS EN TablaIngredientesPorNivel
            ingredientes_nivel = TablaIngredientesPorNivel.objects.filter(id_analisis=analisis)
            print(f"      • Ingredientes configurados: {ingredientes_nivel.count()}")

            if ingredientes_nivel.count() == 0:
                print("      ⚠️  WARNING: No hay ingredientes con pesos guardados para este nivel")
                continue

            # Mostrar detalles de ingredientes con pesos
            total_calorias = 0
            total_proteina = 0
            total_peso_neto = 0

            print(f"\n      INGREDIENTES CON PESOS:")
            for ing in ingredientes_nivel:
                print(f"      • {ing.id_ingrediente_siesa.nombre_ingrediente}")
                print(f"        - Peso neto: {ing.peso_neto}g | Peso bruto: {ing.peso_bruto}g")
                print(f"        - Calorías: {ing.calorias:.1f} kcal | Proteína: {ing.proteina:.1f}g")
                print(f"        - Grasa: {ing.grasa:.1f}g | CHO: {ing.cho:.1f}g")

                total_calorias += float(ing.calorias)
                total_proteina += float(ing.proteina)
                total_peso_neto += float(ing.peso_neto)

            # Totales del análisis
            print(f"\n      TOTALES NUTRICIONALES:")
            print(f"      • Peso neto total: {total_peso_neto:.1f}g")
            print(f"      • Calorías totales: {total_calorias:.1f} kcal")
            print(f"      • Proteína total: {total_proteina:.1f}g")
            print(f"      • Grasa total: {float(analisis.total_grasa or 0):.1f}g")
            print(f"      • CHO total: {float(analisis.total_cho or 0):.1f}g")
            print(f"      • Calcio total: {float(analisis.total_calcio or 0):.1f}mg")
            print(f"      • Hierro total: {float(analisis.total_hierro or 0):.2f}mg")

        print("\n" + "=" * 70)
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print("=" * 70)

        # 7. RESUMEN FINAL
        print(f"\n📈 RESUMEN:")
        print(f"   ✓ Menú creado: {menu.menu}")
        print(f"   ✓ Preparaciones: {preparaciones.count()}")
        print(f"   ✓ Análisis nutricionales (niveles): {analisis_nutricionales.count()}")
        print(f"   ✓ Total ingredientes con pesos: {TablaIngredientesPorNivel.objects.filter(id_analisis__id_menu=menu).count()}")
        print()

    except Exception as e:
        print(f"\n💥 ERROR DURANTE LA PRUEBA:")
        print(f"   {str(e)}")
        import traceback
        print("\nTraceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    test_ia_generation_multinivel()
