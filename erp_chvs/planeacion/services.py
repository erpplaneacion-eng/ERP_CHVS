import cloudinary
import cloudinary.uploader
from django.conf import settings
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class CloudinaryService:
    """
    Servicio para interactuar con Cloudinary de forma explícita.
    Aunque Django Cloudinary Storage maneja la mayoría de los casos automáticamente
    a través de los modelos, este servicio permite operaciones manuales.
    """
    
    @staticmethod
    def subir_imagen(file: Any, folder: str = "programas_imagenes") -> Optional[str]:
        """
        Sube una imagen manualmente a Cloudinary.
        Retorna la URL de la imagen subida o None si falla.
        """
        try:
            upload_result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type="image"
            )
            return upload_result.get("secure_url")
        except Exception as e:
            logger.error(f"Error al subir imagen a Cloudinary: {str(e)}")
            return None

    @staticmethod
    def eliminar_imagen(public_id: str) -> bool:
        """
        Elimina una imagen de Cloudinary usando su public_id.
        """
        try:
            cloudinary.uploader.destroy(public_id)
            return True
        except Exception as e:
            logger.error(f"Error al eliminar imagen de Cloudinary: {str(e)}")
            return False

class ProgramaService:
    """
    Servicio para lógica de negocio relacionada con Programas.
    """
    
    @staticmethod
    def actualizar_imagen_programa(programa_id: int, imagen_file: Any) -> bool:
        """
        Actualiza la imagen de un programa específico.
        """
        from .models import Programa
        try:
            programa = Programa.objects.get(id=programa_id)
            # Al asignar el archivo al campo ImageField con Cloudinary configurado,
            # la subida es automática al guardar el modelo.
            programa.imagen = imagen_file
            programa.save()
            return True
        except Programa.DoesNotExist:
            logger.error(f"Programa con ID {programa_id} no encontrado.")
            return False
        except Exception as e:
            logger.error(f"Error al actualizar imagen del programa: {str(e)}")
            return False
