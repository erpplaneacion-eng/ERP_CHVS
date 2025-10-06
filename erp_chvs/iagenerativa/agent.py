from django.conf import settings
from nutricion.models import TablaIngredientesSiesa, TablaMenus, TablaPreparaciones, TablaPreparacionIngredientes

def generar_menu_con_ingredientes(nombre_menu, id_modalidad, id_contrato):
    """
    Genera un menú con ingredientes usando un modelo de IA generativa.
    """
    # Import lazy para evitar error si no se usa
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "google-generativeai no está instalado. "
            "Instala con: pip install google-generativeai"
        )

    # Verificar que la API Key esté configurada
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY no está configurada. "
            "Agrega GEMINI_API_KEY a tu archivo .env para usar esta funcionalidad."
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Obtener todos los ingredientes de la base de datos
    ingredientes = TablaIngredientesSiesa.objects.all()
    lista_ingredientes = [ing.nombre_ingrediente for ing in ingredientes]

    # Crear el prompt para el modelo generativo
    prompt = (
        f"Eres un chef experto en nutrición para programas de alimentación escolar. "
        f"Crea un menú llamado '{nombre_menu}' que sea balanceado y nutritivo. "
        f"El menú debe incluir 3 preparaciones (desayuno, almuerzo, cena). "
        f"Para cada preparación, utiliza únicamente ingredientes de la siguiente lista: {', '.join(lista_ingredientes)}. "
        f"Formatea la respuesta como un JSON con la siguiente estructura: "
        f"{{'preparaciones': [{{'nombre': 'nombre_preparacion', 'ingredientes': ['ingrediente1', 'ingrediente2']}}]}}"
    )

    # Llamar al modelo generativo
    model = genai.GenerativeModel('gemini-pro-latest')
    response = model.generate_content(prompt)

    # Procesar la respuesta y crear los objetos en la base de datos
    # (Esta parte se implementará en el siguiente paso)

    return response.text
