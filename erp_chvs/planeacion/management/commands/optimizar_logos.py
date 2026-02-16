"""
Comando de Django para optimizar logos existentes de programas.

Uso:
    python manage.py optimizar_logos

Optimiza automáticamente todos los logos de programas existentes:
- Convierte a escala de grises (B/N para impresión)
- Reduce resolución a máximo 400px de ancho
- Comprime con calidad 75%
- Objetivo: logos menores a 50 KB
"""

from django.core.management.base import BaseCommand
from planeacion.models import Programa
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import requests


class Command(BaseCommand):
    help = 'Optimiza los logos de todos los programas existentes (B/N, baja resolución para impresión)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se haría sin modificar nada',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        programas = Programa.objects.filter(imagen__isnull=False).exclude(imagen='')
        total = programas.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('No hay programas con imagen para optimizar'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS(f'🖼️  OPTIMIZADOR DE LOGOS DE PROGRAMAS'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}\n'))
        self.stdout.write(f'Programas a procesar: {total}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODO DRY-RUN: No se modificará nada\n'))

        procesados = 0
        optimizados = 0
        errores = 0

        for programa in programas:
            procesados += 1
            self.stdout.write(f'\n[{procesados}/{total}] Procesando: {programa.programa}')

            try:
                # Obtener la imagen (puede estar en Cloudinary o local)
                imagen_url = programa.imagen.url

                # Si es URL de Cloudinary, descargarla
                if imagen_url.startswith(('http://', 'https://')):
                    self.stdout.write(f'   📥 Descargando desde Cloudinary...')
                    response = requests.get(imagen_url, timeout=30)
                    response.raise_for_status()
                    img_data = BytesIO(response.content)
                    original_size = len(response.content)
                else:
                    # Imagen local
                    img_data = BytesIO(programa.imagen.read())
                    original_size = len(img_data.getvalue())
                    img_data.seek(0)

                self.stdout.write(f'   📊 Tamaño original: {original_size / 1024:.2f} KB')

                # Abrir imagen
                img = Image.open(img_data)
                original_mode = img.mode
                original_width = img.width
                original_height = img.height

                self.stdout.write(f'   🎨 Modo: {original_mode}, Dimensiones: {original_width}x{original_height}')

                # Optimizar
                # 1. Convertir a escala de grises (B/N)
                if img.mode != 'L':
                    img = img.convert('L')
                    self.stdout.write(f'   ⚫ Convertido a escala de grises')

                # 2. Redimensionar a máximo 400px de ancho
                max_width = 400
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                    self.stdout.write(f'   📐 Redimensionado: {original_width}x{original_height} → {max_width}x{new_height}')

                # 3. Comprimir
                output = BytesIO()
                img.save(output, format='JPEG', quality=75, optimize=True)
                output.seek(0)

                optimized_size = len(output.getvalue())
                reduction = 100 - (optimized_size * 100 / original_size)

                self.stdout.write(self.style.SUCCESS(
                    f'   ✅ Optimizado: {original_size / 1024:.2f} KB → {optimized_size / 1024:.2f} KB '
                    f'({reduction:.1f}% reducción)'
                ))

                # Guardar si no es dry-run
                if not dry_run:
                    programa.imagen.save(
                        programa.imagen.name,
                        InMemoryUploadedFile(
                            output,
                            'ImageField',
                            programa.imagen.name,
                            'image/jpeg',
                            sys.getsizeof(output),
                            None
                        ),
                        save=False  # No llamar save() para evitar recursión
                    )
                    # Guardar solo el campo imagen sin triggear el método save() completo
                    programa.save(update_fields=['imagen'])
                    self.stdout.write(self.style.SUCCESS(f'   💾 Guardado en Cloudinary'))

                optimizados += 1

            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))

        # Resumen final
        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS(f'📊 RESUMEN'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}'))
        self.stdout.write(f'Total procesados: {procesados}')
        self.stdout.write(self.style.SUCCESS(f'✅ Optimizados: {optimizados}'))
        if errores > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errores: {errores}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  Modo DRY-RUN: No se modificó nada'))
            self.stdout.write(self.style.WARNING('   Ejecuta sin --dry-run para aplicar los cambios'))
