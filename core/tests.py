from io import StringIO
from unittest.mock import patch

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import RequestFactory, TestCase

from .models import Organizacao, Perfil

User = get_user_model()

ENV_ADMIN = {"ADMIN_USUARIO": "chefe", "ADMIN_SENHA": "senha-forte-123"}


@patch.dict("os.environ", ENV_ADMIN)
class GarantirAdminTests(TestCase):
    def rodar(self):
        call_command("garantir_admin", stdout=StringIO())

    def test_cria_superusuario_com_perfil_de_administrador(self):
        self.rodar()
        admin = User.objects.get(username="chefe")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("senha-forte-123"))
        self.assertEqual(admin.perfil.papel, Perfil.ADMIN)

    def test_cria_a_biblioteca_se_nao_existir(self):
        self.rodar()
        self.assertEqual(Organizacao.objects.count(), 1)

    def test_usa_a_biblioteca_que_ja_existe(self):
        org = Organizacao.objects.create(nome="Biblioteca Central")
        self.rodar()
        self.assertEqual(User.objects.get(username="chefe").perfil.organizacao, org)
        self.assertEqual(Organizacao.objects.count(), 1)

    def test_rodar_de_novo_nao_duplica_e_restaura_a_senha_e_o_papel(self):
        self.rodar()
        admin = User.objects.get(username="chefe")
        admin.set_password("outra")
        admin.is_superuser = False
        admin.save()
        admin.perfil.papel = Perfil.OPERADOR
        admin.perfil.save()

        self.rodar()

        admin.refresh_from_db()
        self.assertEqual(User.objects.filter(username="chefe").count(), 1)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("senha-forte-123"))
        self.assertEqual(admin.perfil.papel, Perfil.ADMIN)

    @patch.dict("os.environ", {"ADMIN_SENHA": ""})
    def test_sem_senha_no_env_da_erro(self):
        with self.assertRaises(CommandError):
            self.rodar()

    def test_admin_fixo_nao_pode_ser_apagado_pelo_admin(self):
        self.rodar()
        admin = User.objects.get(username="chefe")
        outro = User.objects.create_user("outro", password="x")
        request = RequestFactory().get("/")
        request.user = admin
        model_admin = site._registry[User]
        self.assertFalse(model_admin.has_delete_permission(request, admin))
        self.assertTrue(model_admin.has_delete_permission(request, outro))
