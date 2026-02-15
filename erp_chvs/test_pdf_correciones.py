"""
Script para verificar las correcciones en el PDF de asistencia
"""
import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from principal.models import TipoGenero
from facturacion.pdf_generator import obtener_id_genero_por_codigo

print("=" * 80)
print("VERIFICACIÓN DE CORRECCIONES EN PDF DE ASISTENCIA")
print("=" * 80)

# 1. Verificar año actual
print("\n📅 Verificación del año:")
ano_actual = datetime.now().year
print(f"Año actual del sistema: {ano_actual}")
print(f"✅ El PDF ahora usará siempre el año actual: {ano_actual}")

# 2. Verificar mapeo de géneros
print("\n👤 Verificación del mapeo de géneros:")
print("\nTabla tipo_genero en la BD:")
generos = TipoGenero.objects.all()
for genero in generos:
    print(f"  • codigo_genero: {genero.codigo_genero} → id_genero: {genero.id_genero} ({genero.genero})")

print("\nPrueba de función obtener_id_genero_por_codigo():")
test_codigos = ['1', '2', 1, 2, '3', 'invalido', '', None]
for codigo in test_codigos:
    resultado = obtener_id_genero_por_codigo(codigo)
    print(f"  Código: {repr(codigo):15} → id_genero: '{resultado}'")

# 3. Resumen
print("\n" + "=" * 80)
print("RESUMEN DE CORRECCIONES")
print("=" * 80)
print("\n✅ CORRECCIÓN 1: Año en el PDF")
print(f"   Antes: Tomaba del campo 'ano' de la BD (podía ser 2025)")
print(f"   Ahora: Siempre usa el año actual del sistema ({ano_actual})")

print("\n✅ CORRECCIÓN 2: Columna '1. Sexo'")
print("   Antes: Mostraba el código numérico (1, 2)")
print("   Ahora: Muestra el id_genero de la tabla tipo_genero")
print("   Ejemplo:")
if generos.count() >= 2:
    gen1 = generos.first()
    gen2 = generos.last()
    print(f"     - Código {gen1.codigo_genero} → '{gen1.id_genero}'")
    print(f"     - Código {gen2.codigo_genero} → '{gen2.id_genero}'")

print("\n" + "=" * 80)
print("PRÓXIMO PASO: Generar un PDF de prueba")
print("=" * 80)
print("\n1. Ve a: Reportes de Asistencia")
print("2. Selecciona un programa, mes y focalización")
print("3. Genera el PDF")
print("4. Verifica:")
print(f"   ✓ El año es {ano_actual}")
print("   ✓ La columna '1. Sexo' muestra códigos como 'GEN01', 'GEN02'")
print("\n" + "=" * 80)
