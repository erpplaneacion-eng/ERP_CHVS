"""
Script para probar la conexión a la base de datos y verificar tablas.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

def probar_conexion_db():
    """Prueba la conexión a la base de datos."""

    print("🔍 Probando conexión a base de datos...")

    try:
        from django.db import connection
        cursor = connection.cursor()

        # Probar conexión simple
        cursor.execute("SELECT 1")
        resultado = cursor.fetchone()
        print(f"✅ Conexión a base de datos: {resultado}")

        # Verificar tablas existentes
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        """)

        tablas = cursor.fetchall()
        print(f"✅ Tablas encontradas: {len(tablas)}")

        # Buscar tablas de OCR
        tablas_ocr = [tabla[0] for tabla in tablas if 'ocr' in tabla[0]]
        print(f"📋 Tablas OCR encontradas: {tablas_ocr}")

        if tablas_ocr:
            print("✅ Tablas OCR están creadas")
        else:
            print("⚠️ No se encontraron tablas OCR")
            print("💡 Ejecute: python manage.py migrate")

        return True

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def verificar_modelos():
    """Verifica que los modelos se puedan importar."""

    print("\n🔍 Verificando modelos...")

    try:
        from ocr_validation.models import PDFValidation, ValidationError
        print("✅ Modelos importados correctamente")

        # Probar crear una instancia (sin guardar)
        validacion = PDFValidation(
            archivo_nombre="test.pdf",
            sede_educativa="Sede Test",
            mes_atencion="OCTUBRE",
            ano=2025,
            tipo_complemento="CAJMPS"
        )
        print("✅ Modelos se pueden instanciar")

        return True

    except Exception as e:
        print(f"❌ Error con modelos: {e}")
        return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DEL SISTEMA OCR")
    print("=" * 40)

    # Probar conexión DB
    conexion_ok = probar_conexion_db()

    # Probar modelos
    modelos_ok = verificar_modelos()

    print("\n" + "=" * 40)
    if conexion_ok and modelos_ok:
        print("🎉 ¡Sistema listo para usar!")
        print("\n📋 Pasos para usar:")
        print("1. Inicie el servidor: python manage.py runserver")
        print("2. Vaya a: http://localhost:8000/")
        print("3. Navegue a Facturación > Validación OCR")
        print("4. Cargue un PDF diligenciado manualmente")
    else:
        print("❌ Hay problemas que resolver")
        print("\n💡 Soluciones:")
        if not conexion_ok:
            print("- Verifique conexión a PostgreSQL")
            print("- Verifique configuración de base de datos")
        if not modelos_ok:
            print("- Ejecute migraciones: python manage.py migrate")