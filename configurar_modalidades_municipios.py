#!/usr/bin/env python
"""
Script para configurar las modalidades de consumo por municipio
"""
import os
import sys
import django

# Obtener la ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_DIR = os.path.join(BASE_DIR, 'erp_chvs')

# Agregar el directorio del proyecto al path
sys.path.insert(0, DJANGO_DIR)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from principal.models import PrincipalMunicipio, ModalidadesDeConsumo, MunicipioModalidades

# Configuración de modalidades por municipio
CONFIGURACION_MODALIDADES = {
    'SANTIAGO DE CALI': ['1', '2', '3', '4'],  # CAJM, CAJT, CAJMRI, ALMUERZO
    'YUMBO': ['1', '3', '4', '5'],  # CAJM, CAJMRI, ALMUERZO, REFUERZO
    'GUADALAJARA DE BUGA': ['1', '3', '4'],  # CAJM, CAJMRI, ALMUERZO
}

# Nombres de modalidades para referencia
MODALIDADES_NOMBRES = {
    '1': 'CAJM',
    '2': 'CAJT',
    '3': 'CAJMRI',
    '4': 'ALMUERZO',
    '5': 'REFUERZO'
}

print("=" * 80)
print("CONFIGURACIÓN DE MODALIDADES POR MUNICIPIO")
print("=" * 80)

# Limpiar configuración existente
print("\n🗑️  Limpiando configuración anterior...")
MunicipioModalidades.objects.all().delete()
print("✓ Configuración anterior eliminada")

# Configurar modalidades por municipio
print("\n📋 Configurando modalidades por municipio...\n")

for nombre_municipio, modalidades_ids in CONFIGURACION_MODALIDADES.items():
    try:
        # Buscar municipio (case-insensitive)
        municipio = PrincipalMunicipio.objects.get(nombre_municipio__iexact=nombre_municipio)
        print(f"📍 {municipio.nombre_municipio} (ID: {municipio.id})")

        # Asignar modalidades
        for modalidad_id in modalidades_ids:
            try:
                modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

                # Crear relación
                MunicipioModalidades.objects.create(
                    municipio=municipio,
                    modalidad=modalidad
                )

                print(f"   ✓ {modalidad.modalidad} (ID: {modalidad.id_modalidades})")

            except ModalidadesDeConsumo.DoesNotExist:
                print(f"   ❌ Modalidad con ID {modalidad_id} no existe")

        print()

    except PrincipalMunicipio.DoesNotExist:
        print(f"❌ Municipio '{nombre_municipio}' no encontrado en la base de datos")
        print(f"   💡 Verifica el nombre exacto del municipio\n")
    except Exception as e:
        print(f"❌ Error al configurar {nombre_municipio}: {e}\n")

# Mostrar resumen
print("=" * 80)
print("RESUMEN DE CONFIGURACIÓN")
print("=" * 80)

municipios_configurados = MunicipioModalidades.objects.values('municipio').distinct().count()
total_relaciones = MunicipioModalidades.objects.count()

print(f"\n✓ Municipios configurados: {municipios_configurados}")
print(f"✓ Total de relaciones creadas: {total_relaciones}")

# Mostrar configuración detallada
print("\n📊 CONFIGURACIÓN ACTUAL:\n")
for municipio in PrincipalMunicipio.objects.filter(modalidades_configuradas__isnull=False).distinct():
    modalidades = MunicipioModalidades.objects.filter(municipio=municipio).select_related('modalidad')
    print(f"📍 {municipio.nombre_municipio}:")
    for mm in modalidades:
        print(f"   - {mm.modalidad.modalidad} (ID: {mm.modalidad.id_modalidades})")
    print()

# Instrucciones finales
print("=" * 80)
print("✅ CONFIGURACIÓN COMPLETADA")
print("=" * 80)
print("\n📝 Próximos pasos:")
print("1. Ejecutar migraciones: python manage.py makemigrations principal")
print("2. Aplicar migraciones: python manage.py migrate principal")
print("3. La vista de menús ahora mostrará solo las modalidades configuradas por municipio")
print("\n💡 Para agregar más municipios, edita el diccionario CONFIGURACION_MODALIDADES en este script")
print()
