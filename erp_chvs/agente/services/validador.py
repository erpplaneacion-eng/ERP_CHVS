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

    # Mapa código → nombre oficial de la BD
    alimentos_validos = {
        a.codigo: a.nombre_del_alimento
        for a in TablaAlimentos2018Icbf.objects.filter(codigo__in=codigos_sugeridos)
    }
    componentes_validos = set(
        ComponentesAlimentos.objects.filter(
            id_componente__in=componentes_sugeridos
        ).values_list('id_componente', flat=True)
    )

    resultado = []
    for prep in preparaciones:
        ingredientes_validos = []
        descartados = 0

        for ing in prep.get('ingredientes', []):
            codigo = ing.get('codigo_icbf', '')
            nombre_bd = alimentos_validos.get(codigo)
            if nombre_bd:
                # Solo se usa el nombre y código de la BD — se descarta el nombre sugerido por la IA
                ingredientes_validos.append({
                    'codigo_icbf': codigo,
                    'nombre': nombre_bd,
                    'estado_validacion': 'valido',
                    'observaciones': '',
                })
            else:
                descartados += 1

        if not ingredientes_validos:
            estado_prep = 'invalida'
            obs_prep = 'Ningún ingrediente sugerido existe en el catálogo ICBF'
        else:
            estado_prep = 'valida'
            obs_prep = f'{descartados} ingrediente(s) con código inválido fueron descartados.' if descartados else ''

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
            'ingredientes': ingredientes_validos,
        })

    return resultado
