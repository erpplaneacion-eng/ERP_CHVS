"""
Script de prueba para verificar la sincronización de pesos
desde TablaPreparacionIngredientes hacia análisis nutricional.

Uso:
    python test_sincronizacion_pesos.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.models import (
    TablaMenus,
    TablaPreparaciones,
    TablaPreparacionIngredientes,
    TablaIngredientesPorNivel,
    TablaAnalisisNutricionalMenu
)
from nutricion.services import AnalisisNutricionalService
from principal.models import TablaGradosEscolaresUapa


def test_sincronizacion():
    """
    Prueba la sincronización de pesos desde preparaciones a análisis nutricional.
    """
    print("=" * 80)
    print("TEST DE SINCRONIZACIÓN DE PESOS")
    print("=" * 80)

    # 1. Obtener un menú de ejemplo
    menu = TablaMenus.objects.first()
    if not menu:
        print("❌ ERROR: No hay menús en la base de datos")
        return

    print(f"\n✅ Menú de prueba: {menu.menu} (ID: {menu.id_menu})")
    print(f"   Modalidad: {menu.id_modalidad.modalidad if menu.id_modalidad else 'N/A'}")
    print(f"   Programa: {menu.id_contrato.programa if menu.id_contrato else 'N/A'}")

    # 2. Verificar que tiene preparaciones con gramaje
    preparaciones = TablaPreparaciones.objects.filter(id_menu=menu)
    print(f"\n   Total de preparaciones: {preparaciones.count()}")

    ingredientes_con_gramaje = TablaPreparacionIngredientes.objects.filter(
        id_preparacion__id_menu=menu,
        gramaje__isnull=False,
        gramaje__gt=0
    )
    print(f"   Ingredientes con gramaje: {ingredientes_con_gramaje.count()}")

    if ingredientes_con_gramaje.count() == 0:
        print("\n⚠️  ADVERTENCIA: Este menú no tiene ingredientes con gramaje guardado")
        print("   Para probar, primero guarda algunos gramajes en la vista de preparaciones")
        return

    # 3. Mostrar algunos ejemplos de gramajes
    print("\n📊 Ejemplos de gramajes guardados:")
    for ing in ingredientes_con_gramaje[:5]:
        print(f"   - {ing.id_preparacion.preparacion}: "
              f"{ing.id_ingrediente_siesa.nombre_del_alimento} = {ing.gramaje}g")

    # 4. Obtener un nivel escolar
    nivel = TablaGradosEscolaresUapa.objects.first()
    if not nivel:
        print("\n❌ ERROR: No hay niveles escolares en la base de datos")
        return

    print(f"\n✅ Nivel escolar de prueba: {nivel.nivel_escolar_uapa} (ID: {nivel.id_grado_escolar_uapa})")

    # 5. Verificar estado ANTES de sincronizar
    analisis_antes = TablaAnalisisNutricionalMenu.objects.filter(
        id_menu=menu,
        id_nivel_escolar_uapa=nivel
    ).first()

    if analisis_antes:
        ingredientes_antes = TablaIngredientesPorNivel.objects.filter(
            id_analisis=analisis_antes
        ).count()
        print(f"\n📋 Estado ANTES de sincronizar:")
        print(f"   Ingredientes en TablaIngredientesPorNivel: {ingredientes_antes}")
        print(f"   Total calorías: {analisis_antes.total_calorias} Kcal")
    else:
        print(f"\n📋 Estado ANTES: No existe análisis guardado para este nivel")

    # 6. SINCRONIZAR
    print("\n🔄 Sincronizando pesos desde preparaciones...")
    resultado = AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
        id_menu=menu.id_menu,
        id_nivel_escolar=nivel.id_grado_escolar_uapa,
        sobrescribir_existentes=True
    )

    print(f"\n✅ Resultado de sincronización:")
    print(f"   Success: {resultado['success']}")
    print(f"   Mensaje: {resultado['mensaje']}")
    print(f"   Sincronizados: {resultado['sincronizados']}")
    print(f"   Omitidos: {resultado['omitidos']}")
    if resultado['errores']:
        print(f"   Errores: {len(resultado['errores'])}")
        for error in resultado['errores'][:3]:
            print(f"     - {error}")

    # 7. Verificar estado DESPUÉS de sincronizar
    analisis_despues = TablaAnalisisNutricionalMenu.objects.get(
        id_menu=menu,
        id_nivel_escolar_uapa=nivel
    )

    ingredientes_despues = TablaIngredientesPorNivel.objects.filter(
        id_analisis=analisis_despues
    )

    print(f"\n📊 Estado DESPUÉS de sincronizar:")
    print(f"   Ingredientes en TablaIngredientesPorNivel: {ingredientes_despues.count()}")
    print(f"   Total calorías: {analisis_despues.total_calorias} Kcal")
    print(f"   Total proteína: {analisis_despues.total_proteina} g")
    print(f"   Total peso neto: {analisis_despues.total_peso_neto} g")

    # 8. Mostrar algunos ingredientes sincronizados
    print(f"\n📋 Ejemplos de ingredientes sincronizados:")
    for ing in ingredientes_despues[:5]:
        print(f"   - {ing.id_ingrediente_siesa.nombre_ingrediente}:")
        print(f"     Peso neto: {ing.peso_neto}g | Calorías: {ing.calorias} Kcal")

    # 9. Verificar que coinciden los pesos
    print(f"\n🔍 Verificando coincidencia de pesos...")
    coincidencias = 0
    diferencias = 0

    for ing_prep in ingredientes_con_gramaje[:10]:
        ing_nivel = TablaIngredientesPorNivel.objects.filter(
            id_analisis=analisis_despues,
            id_preparacion=ing_prep.id_preparacion,
            id_ingrediente_siesa__id_ingrediente_siesa=ing_prep.id_ingrediente_siesa.codigo
        ).first()

        if ing_nivel:
            if float(ing_nivel.peso_neto) == float(ing_prep.gramaje):
                coincidencias += 1
            else:
                diferencias += 1
                print(f"   ⚠️  Diferencia en {ing_prep.id_ingrediente_siesa.nombre_del_alimento}: "
                      f"Prep={ing_prep.gramaje}g vs Nivel={ing_nivel.peso_neto}g")

    print(f"\n   Coincidencias: {coincidencias}")
    print(f"   Diferencias: {diferencias}")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETADO")
    print("=" * 80)


def test_analisis_con_gramaje():
    """
    Prueba que el análisis nutricional use el gramaje como peso inicial.
    """
    print("\n" + "=" * 80)
    print("TEST DE ANÁLISIS NUTRICIONAL CON GRAMAJE")
    print("=" * 80)

    # Obtener un menú
    menu = TablaMenus.objects.first()
    if not menu:
        print("❌ ERROR: No hay menús en la base de datos")
        return

    print(f"\n✅ Menú de prueba: {menu.menu} (ID: {menu.id_menu})")

    # Obtener análisis completo
    print(f"\n🔄 Obteniendo análisis nutricional completo...")
    resultado = AnalisisNutricionalService.obtener_analisis_completo(menu.id_menu)

    if not resultado['success']:
        print(f"❌ ERROR: {resultado.get('error', 'Error desconocido')}")
        return

    print(f"✅ Análisis obtenido exitosamente")

    # Verificar que use gramajes
    print(f"\n📊 Verificando uso de gramajes en análisis:")

    for nivel_data in resultado['analisis_por_nivel'][:2]:  # Solo primeros 2 niveles
        print(f"\n   Nivel: {nivel_data['nivel_escolar']['nombre']}")

        for prep in nivel_data['preparaciones'][:3]:  # Solo primeras 3 preparaciones
            print(f"   - {prep['nombre']}:")

            for ing in prep['ingredientes'][:2]:  # Solo primeros 2 ingredientes
                peso_neto = ing.get('peso_neto_base', 0)
                print(f"     * {ing['nombre']}: {peso_neto}g")

                # Verificar si el peso coincide con el gramaje guardado
                ing_prep = TablaPreparacionIngredientes.objects.filter(
                    id_preparacion__id_preparacion=prep['id_preparacion'],
                    id_ingrediente_siesa__codigo=ing.get('codigo_icbf', ing.get('id_ingrediente'))
                ).first()

                if ing_prep and ing_prep.gramaje:
                    if float(peso_neto) == float(ing_prep.gramaje):
                        print(f"       ✅ Coincide con gramaje guardado ({ing_prep.gramaje}g)")
                    else:
                        print(f"       ⚠️  Diferencia con gramaje guardado ({ing_prep.gramaje}g)")
                elif float(peso_neto) == 100.0:
                    print(f"       ℹ️  Usando peso por defecto (no hay gramaje guardado)")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETADO")
    print("=" * 80)


if __name__ == '__main__':
    print("\nEjecutando tests de sincronización de pesos...\n")

    try:
        # Test 1: Sincronización explícita
        test_sincronizacion()

        # Test 2: Uso automático en análisis
        test_analisis_con_gramaje()

    except Exception as e:
        print(f"\n❌ ERROR durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
