import google.generativeai as genai
from django.conf import settings
import json
import logging
from ..models import TablaAlimentos2018Icbf

from decimal import Decimal

logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

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
        
        return json.dumps(alimentos_list, ensure_ascii=False, cls=DecimalEncoder)

    def generar_menu(self, niveles_educativos, minuta_patron_contexts):
        """
        Genera una propuesta de menú con pesos específicos para TODOS los niveles educativos.

        Args:
            niveles_educativos: Lista de niveles educativos
            minuta_patron_contexts: Dict con contextos de minuta patrón por nivel

        Returns:
            Dict con menú y pesos por nivel
        """
        from ..models import ComponentesAlimentos
        from .minuta_service import MinutaService
        
        alimentos_ctx = self._get_alimentos_context()
        instrucciones_adicionales = MinutaService.obtener_instrucciones()
        
        # Obtener lista de componentes válidos
        componentes_validos = list(ComponentesAlimentos.objects.values_list('componente', flat=True))

        # Construir contexto de minutas para todos los niveles
        minutas_por_nivel = {}
        for nivel in niveles_educativos:
            if nivel in minuta_patron_contexts:
                minutas_por_nivel[nivel] = minuta_patron_contexts[nivel]

        prompt = f"""
        Eres un Nutricionista Experto del Programa de Alimentación Escolar (PAE) en Colombia.
        Tu tarea es generar un MENÚ DIARIO (un solo día) con PESOS ESPECÍFICOS PARA CADA NIVEL EDUCATIVO.

        NIVELES EDUCATIVOS: {', '.join(niveles_educativos)}

        INSTRUCCIONES TÉCNICAS DE PLANEACIÓN:
        {instrucciones_adicionales}

        REGLAS DE ORO:
        1. Solo usa alimentos de la LISTA DE MATERIAS PRIMAS adjunta.
        2. El aporte nutricional TOTAL del menú debe estar lo más cerca posible del 'aporte_nutricional_promedio_diario' de cada Minuta Patrón.
        3. Respeta los 'requisitos_componentes' (frecuencia y rango de pesos).
        4. IMPORTANTE: Genera pesos diferentes para cada nivel educativo según sus necesidades.
        5. El campo 'componente' DEBE ser uno de los siguientes valores exactos: {', '.join(componentes_validos)}.
        6. Responde ÚNICAMENTE en formato JSON.

        MINUTAS PATRÓN POR NIVEL:
        {json.dumps(minutas_por_nivel, ensure_ascii=False, cls=DecimalEncoder, indent=2)}

        LISTA DE MATERIAS PRIMAS (Código, Nombre, Energía, Prot, Gras, CHO, Ca, Fe, Na):
        {alimentos_ctx}

        FORMATO DE RESPUESTA ESPERADO (JSON):
        {{
            "nombre_menu": "Nombre sugerido para el menú",
            "preparaciones": [
                {{
                    "nombre_preparacion": "Nombre del plato (ej: Arroz con Pollo)",
                    "componente": "Nombre del componente EXACTO de la lista proporcionada",
                    "ingredientes_por_nivel": {{
                        "Preescolar": [
                            {{
                                "codigo_icbf": "Código de la materia prima",
                                "peso_neto": 50
                            }}
                        ],
                        "Primaria (primero, segundo y tercero)": [
                            {{
                                "codigo_icbf": "Código de la materia prima",
                                "peso_neto": 70
                            }}
                        ]
                    }}
                }}
            ]
        }}

        IMPORTANTE: Debes incluir pesos para TODOS los niveles: {', '.join(niveles_educativos)}
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
