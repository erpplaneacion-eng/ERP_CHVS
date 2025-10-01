"""
Comando Django para probar el procesamiento OCR con un PDF real.
"""

import os
import json
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from ocr_validation.services import OCROrchestrator


class Command(BaseCommand):
    help = 'Prueba el procesamiento OCR con un PDF real'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf',
            type=str,
            default='ocr_validation/pdf ocr_organized.pdf',
            help='Ruta al archivo PDF a procesar'
        )

    def handle(self, *args, **options):
        pdf_path = options['pdf']

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🧪 PRUEBA DE PROCESAMIENTO OCR"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"📄 Archivo: {pdf_path}")

        if not os.path.exists(pdf_path):
            self.stdout.write(self.style.ERROR(f"❌ No se encontró el archivo: {pdf_path}"))
            return

        self.stdout.write(f"📊 Tamaño: {os.path.getsize(pdf_path) / 1024:.2f} KB")
        self.stdout.write("=" * 80)

        try:
            # Leer el archivo PDF
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()

            # Crear un UploadedFile simulado
            uploaded_file = SimpleUploadedFile(
                name=os.path.basename(pdf_path),
                content=pdf_content,
                content_type="application/pdf"
            )

            self.stdout.write("\n🚀 Iniciando procesamiento OCR...\n")

            # Crear orquestador y procesar
            orchestrator = OCROrchestrator()
            resultado = orchestrator.process_pdf(uploaded_file, usuario=None)

            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("📊 RESULTADOS DEL PROCESAMIENTO"))
            self.stdout.write("=" * 80)

            if resultado['success']:
                self.stdout.write(self.style.SUCCESS(f"✅ Estado: EXITOSO"))
                self.stdout.write(f"🆔 ID Validación: {resultado.get('validacion_id')}")
                self.stdout.write(f"⏱️  Tiempo: {resultado.get('tiempo_procesamiento', 0):.2f}s")
                self.stdout.write(f"🏫 Sede Educativa: {resultado.get('sede_educativa')}")
                self.stdout.write(f"❌ Total Errores: {resultado.get('total_errores', 0)}")

                # Mostrar errores por severidad
                errores = resultado.get('errores', [])

                criticos = [e for e in errores if e.get('severidad') == 'critico']
                advertencias = [e for e in errores if e.get('severidad') == 'advertencia']
                info = [e for e in errores if e.get('severidad') == 'info']

                self.stdout.write(f"\n📋 Desglose de errores:")
                self.stdout.write(self.style.ERROR(f"   🔴 Críticos: {len(criticos)}"))
                self.stdout.write(self.style.WARNING(f"   🟡 Advertencias: {len(advertencias)}"))
                self.stdout.write(f"   🔵 Info: {len(info)}")

                # Mostrar primeros 10 errores críticos
                if criticos:
                    self.stdout.write(f"\n🔴 Errores Críticos (primeros 10):")
                    for i, error in enumerate(criticos[:10], 1):
                        self.stdout.write(f"   {i}. [{error.get('tipo')}] {error.get('descripcion')}")
                        self.stdout.write(f"      Página: {error.get('pagina')}, Campo: {error.get('campo')}")

                # Mostrar primeras 5 advertencias
                if advertencias:
                    self.stdout.write(f"\n🟡 Advertencias (primeras 5):")
                    for i, error in enumerate(advertencias[:5], 1):
                        self.stdout.write(f"   {i}. [{error.get('tipo')}] {error.get('descripcion')}")

                # Guardar resultado completo en JSON
                output_file = "resultado_ocr_test.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)

                self.stdout.write(f"\n💾 Resultado completo guardado en: {output_file}")

            else:
                self.stdout.write(self.style.ERROR(f"❌ Estado: ERROR"))
                self.stdout.write(self.style.ERROR(f"⚠️  Error: {resultado.get('error')}"))
                self.stdout.write(f"⏱️  Tiempo: {resultado.get('tiempo_procesamiento', 0):.2f}s")

            self.stdout.write("=" * 80)

            if resultado['success']:
                self.stdout.write(self.style.SUCCESS("\n✅ Prueba completada exitosamente\n"))
            else:
                self.stdout.write(self.style.ERROR("\n❌ Prueba falló\n"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n💥 Error en la prueba: {e}"))
            import traceback
            traceback.print_exc()
