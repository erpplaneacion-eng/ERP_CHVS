import json
import os
from django.conf import settings

class MinutaService:
    """
    Servicio para gestionar la lectura y filtrado de la Minuta Patrón 
    desde el archivo JSON.
    """
    
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
        minutas = cls.obtener_todas()
        for m in minutas:
            if m['modalidad'] == modalidad:
                # Si la tabla tiene 'nivel_educativo' directo (Tablas 8-17)
                if 'nivel_educativo' in m and m['nivel_educativo'] == nivel:
                    return m
                # Si la tabla tiene una lista de 'niveles_educativos' (Tabla 18)
                if 'niveles_educativos' in m:
                    for n in m['niveles_educativos']:
                        if n['nivel'] == nivel:
                            # Retornamos un objeto combinado para que la IA tenga el contexto de la modalidad
                            return {
                                "tabla_referencia": m['tabla_referencia'],
                                "modalidad": m['modalidad'],
                                "descripcion": m['descripcion'],
                                **n
                            }
        return None
