"""
Tests para la utilidad de ordenamiento de preparaciones por componente según modalidad.

Cubre:
- Las 6 modalidades con orden definido (20501, 20507, 20502, 020511, 20503, 20510)
- Fallback alfabético para modalidades sin mapa
- Orden alfabético dentro del mismo componente
- Componentes no listados van al final
- sort_preparaciones_objetos (objetos Django mock)
"""

from django.test import SimpleTestCase

from nutricion.utils.orden_componentes import (
    ORDEN_COMPONENTES_POR_MODALIDAD,
    sort_preparaciones_dicts,
    sort_preparaciones_objetos,
)


def _prep_dict(nombre, componente_id):
    return {'nombre': nombre, 'id_componente_id': componente_id}


class MockPrep:
    """Simula un objeto TablaPreparaciones con los campos mínimos."""
    def __init__(self, preparacion, id_componente_id):
        self.preparacion = preparacion
        self.id_componente_id = id_componente_id

    def __repr__(self):
        return f"<Prep {self.preparacion!r} comp={self.id_componente_id!r}>"


# ──────────────────────────────────────────────────────────────────────────────
# 1. Mapa definido
# ──────────────────────────────────────────────────────────────────────────────

class TestMapaDefinido(SimpleTestCase):
    def test_seis_modalidades_definidas(self):
        self.assertEqual(
            set(ORDEN_COMPONENTES_POR_MODALIDAD.keys()),
            {'20501', '20507', '20502', '020511', '20503', '20510'},
        )

    def test_modalidad_20501_orden_correcto(self):
        esperado = ['com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com15']
        self.assertEqual(ORDEN_COMPONENTES_POR_MODALIDAD['20501'], esperado)

    def test_modalidad_20507_igual_a_20501(self):
        self.assertEqual(
            ORDEN_COMPONENTES_POR_MODALIDAD['20507'],
            ORDEN_COMPONENTES_POR_MODALIDAD['20501'],
        )

    def test_modalidad_20502_orden_correcto(self):
        esperado = ['com11', 'com3', 'com12', 'com13', 'com18']
        self.assertEqual(ORDEN_COMPONENTES_POR_MODALIDAD['20502'], esperado)

    def test_modalidad_020511_igual_a_20502(self):
        self.assertEqual(
            ORDEN_COMPONENTES_POR_MODALIDAD['020511'],
            ORDEN_COMPONENTES_POR_MODALIDAD['20502'],
        )

    def test_modalidad_20503_orden_correcto(self):
        esperado = ['com2', 'com7', 'com8', 'com14', 'com9', 'com11', 'com5', 'com6', 'com15']
        self.assertEqual(ORDEN_COMPONENTES_POR_MODALIDAD['20503'], esperado)

    def test_modalidad_20510_igual_a_20503(self):
        self.assertEqual(
            ORDEN_COMPONENTES_POR_MODALIDAD['20510'],
            ORDEN_COMPONENTES_POR_MODALIDAD['20503'],
        )


# ──────────────────────────────────────────────────────────────────────────────
# 2. sort_preparaciones_dicts — modalidades con orden definido
# ──────────────────────────────────────────────────────────────────────────────

class TestSortDicts20501(SimpleTestCase):
    """Modalidad 20501: com1→com2→com3→com4→com5→com6→com15"""

    def setUp(self):
        self.preps = [
            _prep_dict('Agua panela',    'com5'),
            _prep_dict('Arroz con leche','com1'),
            _prep_dict('Carne molida',   'com2'),
            _prep_dict('Mango',          'com4'),
            _prep_dict('Margarina',      'com6'),
            _prep_dict('Pan tajado',     'com3'),
        ]

    def _nombres(self, modalidad):
        return [p['nombre'] for p in sort_preparaciones_dicts(self.preps, modalidad)]

    def test_orden_20501(self):
        self.assertEqual(
            self._nombres('20501'),
            ['Arroz con leche', 'Carne molida', 'Pan tajado', 'Mango', 'Agua panela', 'Margarina'],
        )

    def test_orden_20507_igual_a_20501(self):
        self.assertEqual(self._nombres('20507'), self._nombres('20501'))


class TestSortDicts20502(SimpleTestCase):
    """Modalidad 20502 / 020511: com11→com3→com12→com13"""

    def setUp(self):
        self.preps = [
            _prep_dict('Postre de gelatina', 'com13'),
            _prep_dict('Cereal granola',     'com3'),
            _prep_dict('Leche con cacao',    'com11'),
            _prep_dict('Ensalada de frutas', 'com12'),
        ]

    def _nombres(self, modalidad):
        return [p['nombre'] for p in sort_preparaciones_dicts(self.preps, modalidad)]

    def test_orden_20502(self):
        self.assertEqual(
            self._nombres('20502'),
            ['Leche con cacao', 'Cereal granola', 'Ensalada de frutas', 'Postre de gelatina'],
        )

    def test_orden_020511_igual_a_20502(self):
        self.assertEqual(self._nombres('020511'), self._nombres('20502'))


class TestSortDicts20503(SimpleTestCase):
    """Modalidad 20503 / 20510: com2→com7→com8→com14→com9→com11→com5→com6→com15"""

    def setUp(self):
        self.preps = [
            _prep_dict('Agua panela',     'com5'),
            _prep_dict('Arroz blanco',    'com7'),
            _prep_dict('Frijoles',        'com2'),
            _prep_dict('Jugo de naranja', 'com14'),
            _prep_dict('Leche entera',    'com11'),
            _prep_dict('Aceite vegetal',  'com6'),
            _prep_dict('Papa cocida',     'com8'),
            _prep_dict('Agua',            'com15'),
            _prep_dict('Ensalada roja',   'com9'),
        ]

    def _nombres(self, modalidad):
        return [p['nombre'] for p in sort_preparaciones_dicts(self.preps, modalidad)]

    def test_orden_20503(self):
        self.assertEqual(
            self._nombres('20503'),
            ['Frijoles', 'Arroz blanco', 'Papa cocida',
             'Jugo de naranja', 'Ensalada roja', 'Leche entera', 'Agua panela', 'Aceite vegetal', 'Agua'],
        )

    def test_orden_20510_igual_a_20503(self):
        self.assertEqual(self._nombres('20510'), self._nombres('20503'))


# ──────────────────────────────────────────────────────────────────────────────
# 3. Casos especiales
# ──────────────────────────────────────────────────────────────────────────────

class TestCasosEspeciales(SimpleTestCase):

    def test_componente_fuera_del_mapa_se_omite(self):
        """com9 (Ensalada) no está en el mapa de 20501 → se omite."""
        preps = [
            _prep_dict('Ensalada verde',  'com9'),
            _prep_dict('Arroz con leche', 'com1'),
            _prep_dict('Mango',           'com4'),
        ]
        nombres = [p['nombre'] for p in sort_preparaciones_dicts(preps, '20501')]
        self.assertEqual(nombres, ['Arroz con leche', 'Mango'])

    def test_mismo_componente_orden_alfabetico(self):
        """Dos preparaciones con el mismo componente → orden alfabético entre ellas."""
        preps = [
            _prep_dict('Zumo de lulo',   'com4'),
            _prep_dict('Banano',         'com4'),
            _prep_dict('Mango',          'com4'),
        ]
        nombres = [p['nombre'] for p in sort_preparaciones_dicts(preps, '20501')]
        self.assertEqual(nombres, ['Banano', 'Mango', 'Zumo de lulo'])

    def test_modalidad_sin_mapa_orden_alfabetico(self):
        """Modalidad no definida → fallback alfabético completo."""
        preps = [
            _prep_dict('Zumo',   'com5'),
            _prep_dict('Arroz',  'com2'),
            _prep_dict('Leche',  'com11'),
        ]
        nombres = [p['nombre'] for p in sort_preparaciones_dicts(preps, 'GENERICO')]
        self.assertEqual(nombres, ['Arroz', 'Leche', 'Zumo'])

    def test_modalidad_none_no_falla(self):
        """modalidad_id None no lanza excepción."""
        preps = [_prep_dict('Algo', 'com1')]
        resultado = sort_preparaciones_dicts(preps, None)
        self.assertEqual(len(resultado), 1)

    def test_lista_vacia(self):
        resultado = sort_preparaciones_dicts([], '20501')
        self.assertEqual(resultado, [])

    def test_componente_id_none_se_omite(self):
        """Preparación sin componente asignado (None) → se omite si la modalidad tiene mapa."""
        preps = [
            _prep_dict('Sin componente', None),
            _prep_dict('Arroz con leche', 'com1'),
        ]
        nombres = [p['nombre'] for p in sort_preparaciones_dicts(preps, '20501')]
        self.assertEqual(nombres, ['Arroz con leche'])


# ──────────────────────────────────────────────────────────────────────────────
# 4. sort_preparaciones_objetos (objetos mock)
# ──────────────────────────────────────────────────────────────────────────────

class TestSortObjetos(SimpleTestCase):

    def test_orden_objetos_20501(self):
        preps = [
            MockPrep('Pan tajado',      'com3'),
            MockPrep('Arroz con leche', 'com1'),
            MockPrep('Agua panela',     'com5'),
            MockPrep('Carne molida',    'com2'),
        ]
        resultado = sort_preparaciones_objetos(preps, '20501')
        nombres = [p.preparacion for p in resultado]
        self.assertEqual(nombres, ['Arroz con leche', 'Carne molida', 'Pan tajado', 'Agua panela'])

    def test_orden_objetos_20503(self):
        preps = [
            MockPrep('Leche',   'com11'),
            MockPrep('Frijol',  'com2'),
            MockPrep('Arroz',   'com7'),
        ]
        resultado = sort_preparaciones_objetos(preps, '20503')
        nombres = [p.preparacion for p in resultado]
        self.assertEqual(nombres, ['Frijol', 'Arroz', 'Leche'])

    def test_orden_objetos_sin_mapa_alfabetico(self):
        preps = [
            MockPrep('Zanahoria', 'com9'),
            MockPrep('Arroz',     'com7'),
        ]
        resultado = sort_preparaciones_objetos(preps, '010303')
        nombres = [p.preparacion for p in resultado]
        self.assertEqual(nombres, ['Arroz', 'Zanahoria'])
