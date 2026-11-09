from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Organizacao, Perfil

from .models import Autor, Livro


class IsolamentoBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org_a = Organizacao.objects.create(nome='Biblioteca A')
        cls.org_b = Organizacao.objects.create(nome='Biblioteca B')

        cls.user_a = User.objects.create_user('ana', password='senha-teste-123')
        cls.user_b = User.objects.create_user('bruno', password='senha-teste-123')
        cls.operador_a = User.objects.create_user('otto', password='senha-teste-123')
        Perfil.objects.create(usuario=cls.user_a, organizacao=cls.org_a, papel=Perfil.ADMIN)
        Perfil.objects.create(usuario=cls.user_b, organizacao=cls.org_b, papel=Perfil.ADMIN)
        Perfil.objects.create(usuario=cls.operador_a, organizacao=cls.org_a, papel=Perfil.OPERADOR)

        cls.autor_a = Autor.objects.create(organizacao=cls.org_a, nome='Machado de Assis')
        cls.autor_b = Autor.objects.create(organizacao=cls.org_b, nome='Aluísio Azevedo')

        cls.livro_a = Livro.objects.create(
            organizacao=cls.org_a, titulo='Dom Casmurro',
            autor=cls.autor_a, ano=1899,
        )
        cls.livro_b = Livro.objects.create(
            organizacao=cls.org_b, titulo='O Cortiço',
            autor=cls.autor_b, ano=1890,
        )

    def setUp(self):
        self.client.force_login(self.user_a)

    def dados_livro(self, **extra):
        dados = {
            'titulo': 'Livro Novo', 'autor': self.autor_a.pk, 'ano': 2020,
            'tipo': 'fisico', 'categoria': '800', 'disponivel': True,
        }
        dados.update(extra)
        return dados


class IsolamentoTelasTests(IsolamentoBase):
    def test_lista_mostra_so_livros_da_propria_organizacao(self):
        resposta = self.client.get(reverse('lista'))
        self.assertContains(resposta, 'Dom Casmurro')
        self.assertNotContains(resposta, 'O Cortiço')

    def test_busca_nao_alcanca_outra_organizacao(self):
        resposta = self.client.get(reverse('lista'), {'nome': 'Cortiço'})
        self.assertNotContains(resposta, 'O Cortiço')

    def test_editar_livro_de_outra_organizacao_da_404(self):
        url = reverse('editar_livro', args=[self.livro_b.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, self.dados_livro()).status_code, 404)
        self.livro_b.refresh_from_db()
        self.assertEqual(self.livro_b.titulo, 'O Cortiço')

    def test_excluir_livro_de_outra_organizacao_da_404(self):
        url = reverse('excluir_livro', args=[self.livro_b.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(Livro.objects.filter(pk=self.livro_b.pk).exists())

    def test_criar_livro_grava_na_organizacao_do_usuario(self):
        resposta = self.client.post(
            reverse('novo_livro'), self.dados_livro(organizacao=self.org_b.pk),
        )
        self.assertRedirects(resposta, reverse('lista'))
        livro = Livro.objects.get(titulo='Livro Novo')
        self.assertEqual(livro.organizacao, self.org_a)

    def test_editar_livro_proprio_funciona(self):
        url = reverse('editar_livro', args=[self.livro_a.pk])
        resposta = self.client.post(url, self.dados_livro(titulo='Dom Casmurro (ed. revista)'))
        self.assertRedirects(resposta, reverse('lista'))
        self.livro_a.refresh_from_db()
        self.assertEqual(self.livro_a.titulo, 'Dom Casmurro (ed. revista)')
        self.assertEqual(self.livro_a.organizacao, self.org_a)

    def test_sem_login_redireciona_para_o_login(self):
        self.client.logout()
        resposta = self.client.get(reverse('lista'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('login'), resposta['Location'])

    def test_usuario_sem_perfil_recebe_403(self):
        sem_perfil = User.objects.create_user('carlos', password='senha-teste-123')
        self.client.force_login(sem_perfil)
        self.assertEqual(self.client.get(reverse('lista')).status_code, 403)


class AutorTests(IsolamentoBase):
    def test_select_de_autor_mostra_so_autores_da_organizacao(self):
        resposta = self.client.get(reverse('novo_livro'))
        autores = list(resposta.context['form'].fields['autor'].queryset)
        self.assertEqual(autores, [self.autor_a])

    def test_nao_aceita_autor_de_outra_organizacao_no_formulario(self):
        resposta = self.client.post(
            reverse('novo_livro'), self.dados_livro(autor=self.autor_b.pk),
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('autor', resposta.context['form'].errors)
        self.assertFalse(Livro.objects.filter(titulo='Livro Novo').exists())

    def test_lista_de_autores_mostra_so_os_da_organizacao(self):
        resposta = self.client.get(reverse('autores'))
        self.assertContains(resposta, 'Machado de Assis')
        self.assertNotContains(resposta, 'Aluísio Azevedo')

    def test_cadastrar_autor_grava_na_organizacao_do_usuario(self):
        resposta = self.client.post(reverse('autores'), {'nome': 'Clarice Lispector'})
        self.assertRedirects(resposta, reverse('autores'))
        autor = Autor.objects.get(nome='Clarice Lispector')
        self.assertEqual(autor.organizacao, self.org_a)

    def test_autor_repetido_na_mesma_organizacao_da_erro(self):
        resposta = self.client.post(reverse('autores'), {'nome': 'machado de assis'})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('nome', resposta.context['form'].errors)

    def test_mesmo_autor_em_outra_organizacao_e_permitido(self):
        resposta = self.client.post(reverse('autores'), {'nome': 'Aluísio Azevedo'})
        self.assertRedirects(resposta, reverse('autores'))
        self.assertEqual(Autor.objects.filter(nome='Aluísio Azevedo').count(), 2)


class PapelTests(IsolamentoBase):
    def test_operador_pode_cadastrar_livro(self):
        self.client.force_login(self.operador_a)
        resposta = self.client.post(reverse('novo_livro'), self.dados_livro())
        self.assertRedirects(resposta, reverse('lista'))

    def test_operador_nao_pode_excluir_livro(self):
        self.client.force_login(self.operador_a)
        url = reverse('excluir_livro', args=[self.livro_a.pk])
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Livro.objects.filter(pk=self.livro_a.pk).exists())

    def test_operador_nao_ve_link_de_excluir(self):
        self.client.force_login(self.operador_a)
        resposta = self.client.get(reverse('lista'))
        self.assertNotContains(resposta, 'Excluir')

    def test_admin_pode_excluir_livro(self):
        url = reverse('excluir_livro', args=[self.livro_a.pk])
        self.assertRedirects(self.client.post(url), reverse('lista'))
        self.assertFalse(Livro.objects.filter(pk=self.livro_a.pk).exists())

    def test_operador_nao_pode_excluir_pela_api(self):
        self.client.force_login(self.operador_a)
        resposta = self.client.delete(f'/api/livros/{self.livro_a.pk}/')
        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(Livro.objects.filter(pk=self.livro_a.pk).exists())

    def test_admin_pode_excluir_pela_api(self):
        resposta = self.client.delete(f'/api/livros/{self.livro_a.pk}/')
        self.assertEqual(resposta.status_code, 204)


class IsolamentoApiTests(IsolamentoBase):
    def test_api_lista_so_livros_da_propria_organizacao(self):
        resposta = self.client.get('/api/livros/')
        self.assertEqual(resposta.status_code, 200)
        titulos = [livro['titulo'] for livro in resposta.json()]
        self.assertEqual(titulos, ['Dom Casmurro'])

    def test_api_mostra_nome_do_autor_e_nao_expoe_organizacao(self):
        dados = self.client.get(f'/api/livros/{self.livro_a.pk}/').json()
        self.assertEqual(dados['autor_nome'], 'Machado de Assis')
        self.assertNotIn('organizacao', dados)

    def test_api_detalhe_de_outra_organizacao_da_404(self):
        url = f'/api/livros/{self.livro_b.pk}/'
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.patch(url, {'titulo': 'Hackeado'}, content_type='application/json').status_code,
            404,
        )
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.livro_b.refresh_from_db()
        self.assertEqual(self.livro_b.titulo, 'O Cortiço')

    def test_api_criar_grava_na_organizacao_do_usuario(self):
        resposta = self.client.post(
            '/api/livros/',
            self.dados_livro(organizacao=self.org_b.pk),
            content_type='application/json',
        )
        self.assertEqual(resposta.status_code, 201)
        livro = Livro.objects.get(pk=resposta.json()['id'])
        self.assertEqual(livro.organizacao, self.org_a)

    def test_api_nao_aceita_autor_de_outra_organizacao(self):
        resposta = self.client.post(
            '/api/livros/',
            self.dados_livro(autor=self.autor_b.pk),
            content_type='application/json',
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('autor', resposta.json())

    def test_api_dado_invalido_da_400(self):
        resposta = self.client.post(
            '/api/livros/', {'titulo': 'Sem autor'}, content_type='application/json',
        )
        self.assertEqual(resposta.status_code, 400)

    def test_api_sem_login_e_bloqueada(self):
        self.client.logout()
        self.assertIn(self.client.get('/api/livros/').status_code, (401, 403))
