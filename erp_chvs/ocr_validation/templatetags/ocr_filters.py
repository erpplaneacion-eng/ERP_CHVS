"""
Filtros personalizados para templates de OCR validation.
"""
from django import template
import json
import pprint

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Permite acceder a valores de un diccionario usando una clave.
    Uso: {{ dict|lookup:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def pprint(value):
    """
    Formatea un objeto Python de forma legible.
    Uso: {{ objeto|pprint }}
    """
    try:
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2, ensure_ascii=False)
        return str(value)
    except:
        return str(value)

@register.filter
def get_item(dictionary, key):
    """
    Obtiene un elemento de un diccionario.
    Uso: {{ dict|get_item:key }}
    """
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter
def multiply(value, arg):
    """
    Multiplica un valor por un argumento.
    Uso: {{ valor|multiply:2 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0