import google.generativeai as genai
from django.conf import settings

def list_models():
    """Lists available generative models."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    models_str = ""
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            models_str += f"{m.name}\n"
    return models_str

def generar_menu_con_ingredientes(nombre_menu, id_modalidad, id_contrato):
    """
    Temporarily lists models to debug.
    """
    return list_models()