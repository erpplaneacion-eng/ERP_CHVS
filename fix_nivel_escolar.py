"""
Script para corregir el ID de nivel escolar inválido (-1) en TablaRequerimientosNutricionales
Cambia el ID de -1 a 100
"""

import os
import sys
import django

# Configurar Django
sys.path.append(r'C:\Users\User\OneDrive\Desktop\CHVS\ERP_CHVS\erp_chvs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.models import TablaRequerimientosNutricionales
from principal.models import TablaGradosEscolaresUapa
from django.db import transaction

def main():
    print("=" * 60)
    print("CORRECCIÓN DE NIVEL ESCOLAR EN REQUERIMIENTOS NUTRICIONALES")
    print("=" * 60)

    # 1. Verificar si existe el nivel escolar con ID = 100
    try:
        nivel_100 = TablaGradosEscolaresUapa.objects.get(id_grado_escolar_uapa='100')
        print(f"\n✓ Nivel escolar ID=100 encontrado: {nivel_100.nivel_escolar_uapa}")
    except TablaGradosEscolaresUapa.DoesNotExist:
        print("\n✗ ERROR: No existe el nivel escolar con ID=100")
        print("\nNiveles escolares disponibles:")
        for nivel in TablaGradosEscolaresUapa.objects.all():
            print(f"  - ID: {nivel.id_grado_escolar_uapa} | Nombre: {nivel.nivel_escolar_uapa}")
        return

    # 2. Buscar requerimientos con ID -1
    requerimientos_invalidos = TablaRequerimientosNutricionales.objects.filter(
        id_nivel_escolar_uapa__id_grado_escolar_uapa='-1'
    )

    count = requerimientos_invalidos.count()
    print(f"\n✓ Requerimientos con ID=-1 encontrados: {count}")

    if count == 0:
        print("\n✓ No hay registros que corregir")
        return

    # 3. Mostrar registros a actualizar
    print("\nRegistros a actualizar:")
    for req in requerimientos_invalidos:
        print(f"  - ID Req: {req.id_requerimiento_nutricional} | Calorías: {req.calorias_kcal} Kcal")

    # 4. Confirmar cambio
    confirmacion = input("\n¿Desea cambiar estos registros al nivel escolar ID=100? (s/n): ")

    if confirmacion.lower() != 's':
        print("\n✗ Operación cancelada")
        return

    # 5. Actualizar registros
    try:
        with transaction.atomic():
            actualizados = requerimientos_invalidos.update(id_nivel_escolar_uapa=nivel_100)
            print(f"\n✓ {actualizados} registro(s) actualizado(s) exitosamente")

            # Verificar
            print("\nVerificación:")
            for req in TablaRequerimientosNutricionales.objects.filter(id_nivel_escolar_uapa=nivel_100):
                print(f"  ✓ ID Req: {req.id_requerimiento_nutricional} | Nivel: {req.id_nivel_escolar_uapa.nivel_escolar_uapa}")

    except Exception as e:
        print(f"\n✗ ERROR al actualizar: {e}")
        return

    print("\n" + "=" * 60)
    print("CORRECCIÓN COMPLETADA")
    print("=" * 60)

if __name__ == '__main__':
    main()
