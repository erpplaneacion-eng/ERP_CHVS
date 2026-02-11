import json
import os
from django.conf import settings

class MinutaService:
    """
    Servicio para gestionar la lectura y filtrado de la Minuta Patrón 
    desde el archivo JSON.
    """
    
    # Mapeo de nombres de base de datos a nombres estándar del JSON (Resolución)
    NORMALIZACION_MODALIDADES = {
        'COMPLEMENTO ALIMENTARIO PREPARADO AM': 'Preparada en sitio y comida caliente transportada',
        'COMPLEMENTO ALIMENTARIO PREPARADO PM': 'Preparada en sitio y comida caliente transportada',
        'ALMUERZO JORNADA UNICA': 'Preparada en sitio y comida caliente transportada',
        'REFUERZO COMPLEMENTO AM/PM': 'Preparada en sitio y comida caliente transportada',
        'COMPLEMENTO AM/PM INDUSTRIALIZADO': 'Ración Industrializada',
    }

    # Mapeo de niveles educativos (Base de Datos -> Posibles nombres en JSON)
    NORMALIZACION_NIVELES = {
        'prescolar': ['Preescolar'],
        'primaria_1_2_3': [
            'Primaria (primero, segundo y tercero)', 
            'Primaria (1ro, 2do y 3ro)'
        ],
        'primaria_4_5': [
            'Primaria (cuarto y quinto)', 
            'Primaria (4to y 5to)'
        ],
        'secundaria': ['Secundaria'],
        'media_ciclo_complementario': [
            'Nivel medio y ciclo complementario', 
            'Media y Ciclo Complementario'
        ],
    }
    
    @staticmethod
    def _get_json_path():
        return os.path.join(settings.BASE_DIR, 'nutricion', 'data', 'minuta_patron.json')

    @classmethod
    def obtener_todas(cls):
        with open(cls._get_json_path(), 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def obtener_por_tabla(cls, tabla_referencia):
        minutas = cls.obtener_todas()
        return next((m for m in minutas if m['tabla_referencia'] == tabla_referencia), None)

    @classmethod
    def obtener_por_modalidad_y_nivel(cls, modalidad, nivel):
        """
        Busca una minuta que coincida con la modalidad y el nivel educativo.
        """
        # Normalizar el nombre de la modalidad y nivel si existen en nuestros mapas
        modalidad_estandar = cls.NORMALIZACION_MODALIDADES.get(modalidad, modalidad)
        nivel_estandar = cls.NORMALIZACION_NIVELES.get(nivel, nivel)
        
        minutas = cls.obtener_todas()
        for m in minutas:
            if m['modalidad'] == modalidad_estandar:
                # Si la tabla tiene 'nivel_educativo' directo (Tablas 8-17)
                if 'nivel_educativo' in m and m['nivel_educativo'] == nivel_estandar:
                    return m
                # Si la tabla tiene una lista de 'niveles_educativos' (Tabla 18)
                if 'niveles_educativos' in m:
                    for n in m['niveles_educativos']:
                        if n['nivel'] == nivel_estandar:
                            # Retornamos un objeto combinado para que la IA tenga el contexto de la modalidad
                            return {
                                "tabla_referencia": m['tabla_referencia'],
                                "modalidad": m['modalidad'],
                                "descripcion": m['descripcion'],
                                **n
                            }
        return None
