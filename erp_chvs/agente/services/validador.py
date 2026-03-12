from nutricion.models import TablaAlimentos2018Icbf, ComponentesAlimentos


def validar_preparaciones(preparaciones: list) -> list:
    codigos_sugeridos = set()
    componentes_sugeridos = set()
    for p in preparaciones:
        if p.get('id_componente'):
            componentes_sugeridos.add(p['id_componente'])
        for ing in p.get('ingredientes', []):
            if ing.get('codigo_icbf'):
                codigos_sugeridos.add(ing['codigo_icbf'])

    alimentos_validos = set(
        TablaAlimentos2018Icbf.objects.filter(
            codigo__in=codigos_sugeridos
        ).values_list('codigo', flat=True)
    )
    componentes_validos = set(
        ComponentesAlimentos.objects.filter(
            id_componente__in=componentes_sugeridos
        ).values_list('id_componente', flat=True)
    )

    resultado = []
    for prep in preparaciones:
        ingredientes_validados = []
        tiene_invalido = False

        for ing in prep.get('ingredientes', []):
            codigo = ing.get('codigo_icbf', '')
            if codigo in alimentos_validos:
                estado = 'valido'
                obs = ''
            else:
                estado = 'no_encontrado'
                obs = f"Código '{codigo}' no existe en el catálogo ICBF"
                tiene_invalido = True

            ingredientes_validados.append({
                **ing,
                'estado_validacion': estado,
                'observaciones': obs,
            })

        if not ingredientes_validados:
            estado_prep = 'invalida'
            obs_prep = 'La preparación no tiene ingredientes'
        elif tiene_invalido:
            estado_prep = 'con_duda'
            obs_prep = 'Uno o más ingredientes no están en el catálogo'
        else:
            estado_prep = 'valida'
            obs_prep = ''

        id_componente = prep.get('id_componente')
        if id_componente and id_componente not in componentes_validos:
            id_componente = None

        resultado.append({
            'nombre': prep.get('nombre', ''),
            'id_componente': id_componente,
            'justificacion': prep.get('justificacion', ''),
            'procedimiento': prep.get('procedimiento', ''),
            'estado_validacion': estado_prep,
            'observaciones': obs_prep,
            'ingredientes': ingredientes_validados,
        })

    return resultado
