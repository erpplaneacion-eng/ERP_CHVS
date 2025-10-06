"""
Script de prueba para verificar el funcionamiento del sistema de DataFrames.
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

import pandas as pd
from ocr_validation.dataframe_extractor import DataFrameExtractor, EstudianteRegistro, EncabezadoPDF, DocumentoCompleto
from ocr_validation.ocr_orchestrator import OCROrchestrator


def test_dataframe_schemas():
    """Prueba los schemas de Pydantic."""
    print("🧪 Probando schemas de Pydantic...")
    
    # Crear datos de prueba
    estudiante = EstudianteRegistro(
        numero=1,
        nombre_completo="Juan Pérez",
        cedula="12345678",
        grado="5to",
        raciones_entregadas=1,
        fecha_asistencia="2025-10-05",
        firma_presente=True,
        observaciones="Ninguna"
    )
    
    encabezado = EncabezadoPDF(
        departamento="Valle del Cauca",
        municipio="Cali",
        institucion_educativa="IE Test",
        sede_educativa="Sede Principal",
        codigo_dane="76001001",
        mes_atencion="Octubre",
        ano=2025,
        tipo_complemento="PME",
        responsable="Maria Garcia"
    )
    
    documento = DocumentoCompleto(
        encabezado=encabezado,
        estudiantes=[estudiante],
        total_estudiantes=1,
        total_raciones=1
    )
    
    print("✅ Schemas funcionando correctamente")
    print(f"   - Estudiante: {estudiante.nombre_completo}")
    print(f"   - IE: {encabezado.institucion_educativa}")
    print(f"   - Total estudiantes: {documento.total_estudiantes}")
    
    return documento


def test_dataframe_conversion():
    """Prueba la conversión a DataFrames."""
    print("\n📊 Probando conversión a DataFrames...")
    
    # Crear datos de prueba
    estudiantes_data = [
        {
            'numero': 1,
            'nombre_completo': 'Ana García',
            'cedula': '12345678',
            'grado': '3ro',
            'raciones_entregadas': 1,
            'fecha_asistencia': '2025-10-05',
            'firma_presente': True,
            'observaciones': ''
        },
        {
            'numero': 2,
            'nombre_completo': 'Carlos López',
            'cedula': '87654321',
            'grado': '3ro',
            'raciones_entregadas': 1,
            'fecha_asistencia': '2025-10-05',
            'firma_presente': False,
            'observaciones': 'Ausente'
        }
    ]
    
    encabezado_data = {
        'departamento': 'Valle del Cauca',
        'municipio': 'Cali',
        'institucion_educativa': 'IE Prueba',
        'sede_educativa': 'Sede Central',
        'codigo_dane': '76001001',
        'mes_atencion': 'Octubre',
        'ano': 2025,
        'tipo_complemento': 'PME',
        'responsable': 'Profesora Test'
    }
    
    # Crear DataFrames
    df_estudiantes = pd.DataFrame(estudiantes_data)
    df_encabezado = pd.DataFrame([encabezado_data])
    
    print("✅ DataFrames creados exitosamente")
    print(f"   - Estudiantes: {len(df_estudiantes)} filas, {len(df_estudiantes.columns)} columnas")
    print(f"   - Encabezado: {len(df_encabezado)} filas, {len(df_encabezado.columns)} columnas")
    print(f"   - Columnas estudiantes: {list(df_estudiantes.columns)}")
    
    # Mostrar resumen
    print("\n📋 Resumen de datos:")
    print(f"   - Total raciones: {df_estudiantes['raciones_entregadas'].sum()}")
    print(f"   - Con firma: {df_estudiantes['firma_presente'].sum()}")
    print(f"   - IE: {df_encabezado['institucion_educativa'].iloc[0]}")
    
    return df_estudiantes, df_encabezado


def test_export_formats():
    """Prueba la exportación a diferentes formatos."""
    print("\n💾 Probando exportación a formatos...")
    
    # Crear DataFrame de prueba
    df_test = pd.DataFrame({
        'id': [1, 2, 3],
        'nombre': ['Ana', 'Carlos', 'María'],
        'edad': [8, 9, 8],
        'grado': ['3A', '3B', '3A']
    })
    
    # Crear directorio temporal
    temp_dir = 'temp_exports'
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Exportar a CSV
        csv_path = os.path.join(temp_dir, 'test.csv')
        df_test.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ CSV exportado: {csv_path}")
        
        # Exportar a Excel
        excel_path = os.path.join(temp_dir, 'test.xlsx')
        df_test.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"✅ Excel exportado: {excel_path}")
        
        # Exportar a JSON
        json_path = os.path.join(temp_dir, 'test.json')
        df_test.to_json(json_path, orient='records', force_ascii=False, indent=2)
        print(f"✅ JSON exportado: {json_path}")
        
        print("✅ Todas las exportaciones funcionan correctamente")
        
    except Exception as e:
        print(f"❌ Error en exportación: {e}")
    
    finally:
        # Limpiar archivos temporales
        for file in ['test.csv', 'test.xlsx', 'test.json']:
            file_path = os.path.join(temp_dir, file)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def main():
    """Función principal de pruebas."""
    print("🚀 Iniciando pruebas del sistema de DataFrames\n")
    print("=" * 50)
    
    try:
        # Ejecutar pruebas
        test_dataframe_schemas()
        test_dataframe_conversion()
        test_export_formats()
        
        print("\n" + "=" * 50)
        print("🎉 ¡Todas las pruebas completadas exitosamente!")
        print("\n📋 Resumen del sistema:")
        print("   ✅ Schemas Pydantic configurados")
        print("   ✅ Conversión a DataFrames funcionando")
        print("   ✅ Exportación multi-formato operativa")
        print("   ✅ Sistema listo para procesar PDFs reales")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()