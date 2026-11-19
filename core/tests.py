from io import StringIO
from unittest.mock import patch

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import RequestFactory, TestCase
from django.urls import reverse

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


class CadastroTests(TestCase):
    def dados(self, **extra):
        dados = {
            "username": "nova",
            "email": "nova@exemplo.com",
            "password1": "senha-bem-forte-123",
            "password2": "senha-bem-forte-123",
        }
        dados.update(extra)
        return dados

    def test_pagina_de_cadastro_abre(self):
        self.assertEqual(self.client.get(reverse("cadastro")).status_code, 200)

    def test_cadastro_cria_operador_na_biblioteca_principal_e_faz_login(self):
        org = Organizacao.objects.create(nome="Biblioteca Central")
        resposta = self.client.post(reverse("cadastro"), self.dados())
        self.assertRedirects(resposta, reverse("inicio"))

        usuario = User.objects.get(username="nova")
        self.assertEqual(usuario.perfil.organizacao, org)
        self.assertEqual(usuario.perfil.papel, Perfil.OPERADOR)
        self.assertFalse(usuario.is_staff)
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)

    def test_cadastro_mostra_mensagem_de_boas_vindas(self):
        resposta = self.client.post(reverse("cadastro"), self.dados(), follow=True)
        self.assertContains(resposta, "Conta criada. Bem-vindo(a), nova!")

    def test_cadastro_cria_a_biblioteca_se_nao_existir(self):
        self.client.post(reverse("cadastro"), self.dados())
        self.assertEqual(Organizacao.objects.count(), 1)

    def test_usuario_repetido_da_erro(self):
        User.objects.create_user("nova", password="x")
        resposta = self.client.post(reverse("cadastro"), self.dados())
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("username", resposta.context["form"].errors)

    def test_senhas_diferentes_dao_erro(self):
        resposta = self.client.post(reverse("cadastro"), self.dados(password2="outra-senha-456"))
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(User.objects.filter(username="nova").exists())

    def test_quem_ja_esta_logado_vai_para_o_inicio(self):
        usuario = User.objects.create_user("logado", password="x")
        self.client.force_login(usuario)
        self.assertRedirects(
            self.client.get(reverse("cadastro")), reverse("inicio"), fetch_redirect_response=False,
        )
