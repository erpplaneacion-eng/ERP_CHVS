import google.generativeai as genai
from django.conf import settings
import json
import logging
from ..models import TablaAlimentos2018Icbf

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Servicio para interactuar con Google Gemini AI para la generación 
    automatizada de menús nutricionales.
    """

    def __init__(self):
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.error("GEMINI_API_KEY no configurada en settings.")
            raise ValueError("GEMINI_API_KEY no configurada en settings.")
        
        genai.configure(api_key=api_key)
        # Usamos gemini-2.5-flash, que es el modelo estable más reciente según la documentación
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def _get_alimentos_context(self):
        """
        Extrae y formatea los alimentos de la base de datos para enviarlos como contexto.
        Solo enviamos los campos esenciales para ahorrar tokens.
        """
        alimentos = TablaAlimentos2018Icbf.objects.all().values(
            'codigo', 'nombre_del_alimento', 'energia_kcal', 'proteina_g', 
            'lipidos_g', 'carbohidratos_totales_g', 'calcio_mg', 'hierro_mg', 'sodio_mg'
        )
        
        # Formateamos como una lista compacta para el prompt
        alimentos_list = []
        for a in alimentos:
            alimentos_list.append({
                "id": a['codigo'],
                "n": a['nombre_del_alimento'],
                "e": a['energia_kcal'],
                "p": a['proteina_g'],
                "g": a['lipidos_g'],
                "c": a['carbohidratos_totales_g'],
                "ca": a['calcio_mg'],
                "fe": a['hierro_mg'],
                "na": a['sodio_mg']
            })
        
        return json.dumps(alimentos_list, ensure_ascii=False)

    def generar_menu(self, nivel_educativo, minuta_patron_context):
        """
        Genera una propuesta de menú basada en el nivel educativo y la minuta patrón.
        """
        alimentos_ctx = self._get_alimentos_context()
        
        prompt = f"""
        Eres un Nutricionista Experto del Programa de Alimentación Escolar (PAE) en Colombia.
        Tu tarea es generar un MENÚ DIARIO (un solo día) que cumpla ESTRICTAMENTE con la Minuta Patrón y los requerimientos nutricionales.

        NIVEL EDUCATIVO: {nivel_educativo}
        
        REGLAS DE ORO:
        1. Solo usa alimentos de la LISTA DE MATERIAS PRIMAS adjunta.
        2. El aporte nutricional TOTAL del menú debe estar lo más cerca posible del 'aporte_nutricional_minimo' de la Minuta Patrón.
        3. Respeta los 'requisitos_componentes' (frecuencia y detalle).
        4. Responde ÚNICAMENTE en formato JSON.

        MINUTA PATRÓN (Contexto):
        {json.dumps(minuta_patron_context, ensure_ascii=False)}

        LISTA DE MATERIAS PRIMAS (Código, Nombre, Energía, Prot, Gras, CHO, Ca, Fe, Na):
        {alimentos_ctx}

        FORMATO DE RESPUESTA ESPERADO (JSON):
        {{
            "nombre_menu": "Nombre sugerido para el menú",
            "preparaciones": [
                {{
                    "nombre_preparacion": "Nombre del plato (ej: Arroz con Pollo)",
                    "componente": "Nombre del componente según Minuta Patrón",
                    "ingredientes": [
                        {{
                            "codigo_icbf": "Código de la materia prima",
                            "peso_neto_sugerido": 50
                        }}
                    ]
                }}
            ]
        }}
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2, # Baja temperatura para mayor precisión
                    response_mime_type="application/json"
                )
            )
            
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error al llamar a Gemini: {str(e)}")
            return None
