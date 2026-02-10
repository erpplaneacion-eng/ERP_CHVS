
import os
import django
import json

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.services.menu_service import MenuService
from nutricion.services.gemini_service import GeminiService
from nutricion.models import TablaMenus
from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo

def test_ia_generation():
    print("🚀 Iniciando prueba técnica de Gemini AI...")
    
    # 1. Asegurar datos base
    programa = Programa.objects.first()
    if not programa:
        print("❌ No hay programas en la base de datos.")
        return

    # Usar el nombre exacto que espera el JSON de Minutas
    modalidad_nombre = "Preparada en sitio y comida caliente transportada"
    modalidad, _ = ModalidadesDeConsumo.objects.get_or_create(
        id_modalidades="TEST_IA",
        defaults={"modalidad": modalidad_nombre}
    )
    
    nivel = "Preescolar"
    
    print(f"📋 Parámetros de prueba:")
    print(f"   - Programa: {programa.programa} (ID: {programa.id})")
    print(f"   - Modalidad: {modalidad.modalidad}")
    print(f"   - Nivel: {nivel}")
    print("-" * 30)

    try:
        # 2. Probar generación
        print("🤖 Llamando a Gemini (esto puede tardar unos segundos)...")
        menu = MenuService.generar_menu_con_ia(
            id_programa=programa.id,
            id_modalidad=modalidad.id_modalidades,
            nivel_educativo=nivel
        )

        if menu:
            print("✅ ¡ÉXITO! Menú generado y guardado.")
            print(f"   - Nombre del Menú: {menu.menu}")
            print(f"   - ID en DB: {menu.id_menu}")
            
            # Usamos el related_name 'preparaciones' definido en el modelo
            preparaciones = menu.preparaciones.all()
            print(f"   - Preparaciones generadas ({preparaciones.count()}):")
            for prep in preparaciones:
                # Usamos el related_name 'ingredientes' definido en el modelo
                relaciones_ing = prep.ingredientes.all()
                ings_nombres = [rel.id_ingrediente_siesa.nombre_ingrediente for rel in relaciones_ing]
                print(f"     * [{prep.id_componente.componente if prep.id_componente else 'N/A'}] {prep.preparacion}:")
                print(f"       Ingredientes: {', '.join(ings_nombres)}")
        else:
            print("❌ La IA no devolvió una propuesta válida.")

    except Exception as e:
        print(f"💥 ERROR DURANTE LA PRUEBA: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ia_generation()
