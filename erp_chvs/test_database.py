"""
Script para probar el guardado en base de datos sin procesar PDF real.
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from ocr_validation.ocr_orchestrator import OCROrchestrator
from ocr_validation.models import PDFValidation
from django.contrib.auth.models import User


def test_database_save():
    """Prueba el guardado en base de datos con datos simulados."""
    print("🧪 Probando guardado en base de datos...")
    
    try:
        # Crear orquestador
        orchestrator = OCROrchestrator()
        
        # Datos simulados
        datos_json = {
            'encabezado': {
                'departamento': 'Valle del Cauca',
                'municipio': 'Cali',
                'institucion_educativa': 'IE Test',
                'sede_educativa': 'Sede Principal',
                'codigo_dane': '76001001',
                'mes_atencion': 'Octubre',
                'ano': 2025,
                'tipo_complemento': 'PME',
                'responsable': 'Test User'
            },
            'estudiantes': [
                {
                    'numero': 1,
                    'nombre_completo': 'Test Student',
                    'cedula': '12345678',
                    'grado': '3A',
                    'raciones_entregadas': 1,
                    'fecha_asistencia': '2025-10-05',
                    'firma_presente': True,
                    'observaciones': ''
                }
            ]
        }
        
        metadatos = {
            'total_estudiantes': 1,
            'total_raciones': 1,
            'texto_original_length': 1000,
            'chunks_procesados': 1
        }
        
        resumen = {
            'total_estudiantes': 1,
            'total_raciones': 1,
            'calidad_extraccion': 'buena'
        }
        
        # Obtener o crear usuario de prueba
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com'}
        )
        
        # Probar guardado
        validation_id = orchestrator._guardar_en_db(
            pdf_path='/tmp/test.pdf',
            datos_json=datos_json,
            metadatos=metadatos,
            texto_completo='Texto de prueba completo...',
            resumen=resumen,
            usuario=user
        )
        
        print(f"✅ Guardado exitoso con ID: {validation_id}")
        
        # Verificar que se guardó correctamente
        validation = PDFValidation.objects.get(id=validation_id)
        print(f"📄 Archivo: {validation.archivo_nombre}")
        print(f"🏫 Sede: {validation.sede_educativa}")
        print(f"📅 Mes: {validation.mes_atencion}")
        print(f"📊 Estado: {validation.estado}")
        print(f"🤖 Método: {validation.metodo_ocr}")
        print(f"👤 Usuario: {validation.usuario_creador}")
        
        # Verificar datos JSON
        if validation.datos_estructurados:
            estudiantes_count = len(validation.datos_estructurados.get('estudiantes', []))
            print(f"👥 Estudiantes en JSON: {estudiantes_count}")
        
        print("✅ Verificación completada exitosamente")
        
        return validation_id
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_retrieve_data(validation_id):
    """Prueba la recuperación de datos."""
    print(f"\n🔍 Probando recuperación de datos para ID: {validation_id}")
    
    try:
        orchestrator = OCROrchestrator()
        resultado = orchestrator.get_processing_results(validation_id)
        
        if resultado['success']:
            print(f"✅ Recuperación exitosa")
            print(f"📊 DataFrame estudiantes: {len(resultado['df_estudiantes'])} filas")
            print(f"📋 DataFrame encabezado: {len(resultado['df_encabezado'])} filas")
            print(f"📄 Datos JSON disponibles: {'Sí' if resultado['datos_json'] else 'No'}")
        else:
            print(f"❌ Error en recuperación: {resultado['error']}")
            
    except Exception as e:
        print(f"❌ Error en recuperación: {e}")


def main():
    """Función principal de pruebas."""
    print("🚀 Iniciando pruebas de base de datos")
    print("=" * 50)
    
    # Probar guardado
    validation_id = test_database_save()
    
    if validation_id:
        # Probar recuperación
        test_retrieve_data(validation_id)
        
        print("\n" + "=" * 50)
        print("🎉 ¡Todas las pruebas completadas!")
        print(f"🆔 ID de validación creado: {validation_id}")
        print("✅ El guardado en base de datos funciona correctamente")
    else:
        print("\n❌ Las pruebas fallaron")


if __name__ == "__main__":
    main()