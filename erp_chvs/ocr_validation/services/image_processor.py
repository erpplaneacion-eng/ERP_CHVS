"""
Servicio para preprocesamiento de imágenes.
Mejora la calidad de las imágenes antes del OCR mediante técnicas de procesamiento digital.
"""

from PIL import Image, ImageEnhance
from typing import Union

from .base import BaseOCRService


class ImageProcessorService(BaseOCRService):
    """
    Servicio para preprocesar imágenes antes del OCR.
    Aplica mejoras de calidad para optimizar el reconocimiento de texto.
    """

    def __init__(
        self,
        scale_factor: float = 2.0,
        contrast_factor: float = 2.5,
        sharpness_factor: float = 3.0,
        brightness_factor: float = 1.2,
        **kwargs
    ):
        """
        Inicializa el servicio de procesamiento de imágenes.

        Args:
            scale_factor: Factor de escala para upscaling (2.0 = doble tamaño)
            contrast_factor: Factor de mejora de contraste
            sharpness_factor: Factor de mejora de nitidez
            brightness_factor: Factor de mejora de brillo
        """
        super().__init__(**kwargs)
        self.scale_factor = scale_factor
        self.contrast_factor = contrast_factor
        self.sharpness_factor = sharpness_factor
        self.brightness_factor = brightness_factor

    def process_image(self, image_path: str) -> Image.Image:
        """
        Procesa una imagen para mejorar la calidad del OCR.

        Args:
            image_path: Ruta a la imagen a procesar

        Returns:
            Image.Image: Imagen procesada y mejorada
        """
        try:
            self.log_debug(f"🖼️ Procesando imagen: {image_path}")

            # Cargar imagen
            image = Image.open(image_path)
            original_size = image.size
            self.log_debug(f"  Tamaño original: {original_size[0]}x{original_size[1]}")

            # 1. Convertir a RGB si es necesario
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
                self.log_debug(f"  ✓ Convertida a RGB")

            # 2. Upscaling (aumentar resolución)
            if self.scale_factor > 1.0:
                new_size = (
                    int(original_size[0] * self.scale_factor),
                    int(original_size[1] * self.scale_factor)
                )
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                self.log_debug(f"  ✓ Escalada: {original_size} → {new_size}")

            # 3. Convertir a escala de grises
            if image.mode != 'L':
                image = image.convert('L')
                self.log_debug(f"  ✓ Convertida a escala de grises")

            # 4. Mejorar contraste
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(self.contrast_factor)
            self.log_debug(f"  ✓ Contraste mejorado ({self.contrast_factor}x)")

            # 5. Mejorar nitidez
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(self.sharpness_factor)
            self.log_debug(f"  ✓ Nitidez mejorada ({self.sharpness_factor}x)")

            # 6. Mejorar brillo
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(self.brightness_factor)
            self.log_debug(f"  ✓ Brillo mejorado ({self.brightness_factor}x)")

            self.log_info(f"✅ Imagen procesada exitosamente")
            return image

        except Exception as e:
            self.log_warning(f"⚠️ Error procesando imagen: {e}")
            # Retornar imagen original en caso de error
            return Image.open(image_path)

    def process_and_save(self, input_path: str, output_path: str = None) -> str:
        """
        Procesa una imagen y la guarda en disco.

        Args:
            input_path: Ruta a la imagen de entrada
            output_path: Ruta donde guardar la imagen procesada (opcional)

        Returns:
            str: Ruta de la imagen procesada
        """
        import tempfile

        processed_image = self.process_image(input_path)

        if output_path is None:
            tmp_file = tempfile.NamedTemporaryFile(suffix='_processed.png', delete=False)
            output_path = tmp_file.name
            tmp_file.close()

        processed_image.save(output_path, 'PNG')
        self.log_debug(f"💾 Imagen procesada guardada en: {output_path}")

        return output_path
