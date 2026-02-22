"""
Template tags para verificar pertenencia a grupos de usuarios.
"""
from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_names):
    """
    Verifica si el usuario pertenece a alguno de los grupos especificados.

    Uso en template:
        {% if user|has_group:"NUTRICION,ADMINISTRACION" %}

    Args:
        user: Usuario de Django
        group_names: String con nombres de grupos separados por coma

    Returns:
        bool: True si el usuario pertenece a alguno de los grupos
    """
    if user.is_superuser:
        return True

    if not group_names:
        return False

    # Convertir string a lista normalizada de grupos
    grupos_buscar = [g.strip().upper() for g in group_names.split(',') if g.strip()]

    if not grupos_buscar:
        return False

    # Obtener grupos del usuario (normalizados)
    user_groups = {
        str(group).strip().upper()
        for group in user.groups.values_list('name', flat=True)
    }

    # Verificar si alguno de los grupos del usuario coincide
    return any(grupo in user_groups for grupo in grupos_buscar)
