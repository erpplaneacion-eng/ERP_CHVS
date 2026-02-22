from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from principal.middleware import RoleAccessMiddleware
from principal.templatetags.group_tags import has_group


class GroupTagTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="multi", password="test123")
        self.user.groups.add(
            Group.objects.create(name="NUTRICION"),
            Group.objects.create(name="FACTURACION"),
        )

    def test_has_group_acepta_grupo_simple(self):
        self.assertTrue(has_group(self.user, "NUTRICION"))

    def test_has_group_acepta_lista_de_grupos(self):
        self.assertTrue(has_group(self.user, "PLANEACION, FACTURACION"))

    def test_has_group_es_robusto_a_mayusculas_y_espacios(self):
        self.assertTrue(has_group(self.user, "  nutricion , planeacion "))


class RoleAccessMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RoleAccessMiddleware(lambda request: HttpResponse("ok"))

    def _request_with_user(self, path, user):
        request = self.factory.get(path)
        request.user = user
        return self.middleware(request)

    def test_usuario_con_dos_grupos_tiene_acceso_a_ambos_modulos(self):
        user = User.objects.create_user(username="dual", password="test123")
        user.groups.add(
            Group.objects.create(name="NUTRICION"),
            Group.objects.create(name="FACTURACION"),
        )

        nutrition_response = self._request_with_user("/nutricion/", user)
        billing_response = self._request_with_user("/facturacion/", user)

        self.assertEqual(nutrition_response.status_code, 200)
        self.assertEqual(billing_response.status_code, 200)

    def test_grupo_costos_tiene_acceso_a_modulo_costos(self):
        user = User.objects.create_user(username="cost_user", password="test123")
        user.groups.add(Group.objects.create(name="COSTOS"))

        response = self._request_with_user("/costos/", user)

        self.assertEqual(response.status_code, 200)

    @patch("principal.middleware.messages.error")
    def test_sin_permiso_redirige_al_dashboard(self, _messages_error):
        user = User.objects.create_user(username="limited", password="test123")
        user.groups.add(Group.objects.create(name="FACTURACION"))

        response = self._request_with_user("/nutricion/", user)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")
