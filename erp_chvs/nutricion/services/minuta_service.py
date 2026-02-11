import json
import os
from django.conf import settings

class MinutaService:
    """
    Servicio para gestionar la lectura y filtrado de la Minuta Patrón 
    desde el archivo JSON jerárquico.
    """
    
    # Mapeo de modalidades para asegurar coincidencia con el JSON
    NORMALIZACION_MODALIDADES = {
        'COMPLEMENTO ALIMENTARIO PREPARADO AM': 'COMPLEMENTO ALIMENTARIO PREPARADO AM',
        'COMPLEMENTO ALIMENTARIO PREPARADO PM': 'COMPLEMENTO ALIMENTARIO PREPARADO AM',
        'REFUERZO COMPLEMENTO AM/PM': 'COMPLEMENTO ALIMENTARIO PREPARADO AM',
        'ALMUERZO JORNADA UNICA': 'ALMUERZO JORNADA UNICA',
        'COMPLEMENTO AM/PM INDUSTRIALIZADO': 'COMPLEMENTO AM/PM INDUSTRIALIZADO',
    }

    @staticmethod
    def _get_json_path():
        return os.path.join(settings.BASE_DIR, 'nutricion', 'data', 'minuta_patron.json')

    @classmethod
    def obtener_estructura_completa(cls):
        """Retorna el diccionario completo del JSON."""
        with open(cls._get_json_path(), 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def obtener_todas(cls):
        """
        Mantiene compatibilidad con código anterior pero retorna 
        la sección de categorías.
        """
        data = cls.obtener_estructura_completa()
        return data.get('categorias', {})

    @classmethod
    def obtener_instrucciones(cls):
        """Retorna las instrucciones de planeación del nutricionista."""
        data = cls.obtener_estructura_completa()
        return data.get('instrucciones_planeacion', "")

    @classmethod
    def obtener_por_modalidad_y_nivel(cls, modalidad, nivel):
        """
        Busca una minuta que coincida con la modalidad y el nivel educativo 
        navegando la estructura jerárquica: Categoría -> Modalidad -> Nivel.
        """
        # Normalizar el nombre de la modalidad
        modalidad_estandar = cls.NORMALIZACION_MODALIDADES.get(modalidad, modalidad)
        
        categorias = cls.obtener_todas()
        
        # Recorrer categorías (ej: "Complemento Alimentario Preparado (AM/PM)")
        for desc, modalidades in categorias.items():
            if modalidad_estandar in modalidades:
                nivel_data = modalidades[modalidad_estandar].get(nivel)
                if nivel_data:
                    # Retornamos un objeto plano para compatibilidad con el resto del sistema
                    return {
                        "modalidad": modalidad_estandar,
                        "descripcion": desc,
                        "nivel_educativo": nivel,
                        **nivel_data
                    }
        return None
