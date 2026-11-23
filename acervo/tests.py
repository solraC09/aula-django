from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

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


class EditarExcluirAutorTests(IsolamentoBase):
    def test_editar_autor_proprio_funciona(self):
        url = reverse('editar_autor', args=[self.autor_a.pk])
        resposta = self.client.post(url, {'nome': 'Joaquim Maria Machado de Assis'})
        self.assertRedirects(resposta, reverse('autores'))
        self.autor_a.refresh_from_db()
        self.assertEqual(self.autor_a.nome, 'Joaquim Maria Machado de Assis')

    def test_editar_mantendo_o_mesmo_nome_nao_da_erro_de_repetido(self):
        url = reverse('editar_autor', args=[self.autor_a.pk])
        resposta = self.client.post(url, {'nome': 'Machado de Assis'})
        self.assertRedirects(resposta, reverse('autores'))

    def test_editar_para_nome_de_outro_autor_da_erro(self):
        Autor.objects.create(organizacao=self.org_a, nome='Clarice Lispector')
        url = reverse('editar_autor', args=[self.autor_a.pk])
        resposta = self.client.post(url, {'nome': 'clarice lispector'})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('nome', resposta.context['form'].errors)

    def test_editar_autor_de_outra_organizacao_da_404(self):
        url = reverse('editar_autor', args=[self.autor_b.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'nome': 'Hackeado'}).status_code, 404)

    def test_excluir_autor_sem_livros(self):
        autor = Autor.objects.create(organizacao=self.org_a, nome='Sem Livros')
        url = reverse('excluir_autor', args=[autor.pk])
        self.assertRedirects(self.client.post(url), reverse('autores'))
        self.assertFalse(Autor.objects.filter(pk=autor.pk).exists())

    def test_nao_exclui_autor_que_tem_livros(self):
        url = reverse('excluir_autor', args=[self.autor_a.pk])
        resposta = self.client.post(url)
        self.assertContains(resposta, 'Não é possível excluir')
        self.assertTrue(Autor.objects.filter(pk=self.autor_a.pk).exists())

    def test_excluir_autor_de_outra_organizacao_da_404(self):
        url = reverse('excluir_autor', args=[self.autor_b.pk])
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_operador_nao_pode_excluir_autor(self):
        autor = Autor.objects.create(organizacao=self.org_a, nome='Sem Livros')
        self.client.force_login(self.operador_a)
        url = reverse('excluir_autor', args=[autor.pk])
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Autor.objects.filter(pk=autor.pk).exists())

    def test_lista_de_autores_mostra_quantos_livros_cada_um_tem(self):
        resposta = self.client.get(reverse('autores'))
        autor = resposta.context['autores'].get(pk=self.autor_a.pk)
        self.assertEqual(autor.total_livros, 1)


class BotaoVoltarTests(IsolamentoBase):
    def test_autores_sem_next_volta_para_a_lista(self):
        resposta = self.client.get(reverse('autores'))
        self.assertEqual(resposta.context['voltar_para'], reverse('lista'))

    def test_autores_vindo_do_formulario_volta_para_o_formulario(self):
        resposta = self.client.get(reverse('autores'), {'next': reverse('novo_livro')})
        self.assertEqual(resposta.context['voltar_para'], reverse('novo_livro'))

    def test_autores_ignora_next_para_outro_site(self):
        resposta = self.client.get(reverse('autores'), {'next': 'https://site-malicioso.com/'})
        self.assertEqual(resposta.context['voltar_para'], reverse('lista'))

    def test_cadastrar_autor_mantem_o_caminho_de_volta(self):
        url = reverse('autores') + '?next=' + reverse('novo_livro')
        resposta = self.client.post(url, {'nome': 'Clarice Lispector'})
        self.assertRedirects(resposta, url)

    def test_lista_tem_botao_de_voltar_ao_inicio(self):
        resposta = self.client.get(reverse('lista'))
        self.assertContains(resposta, 'Voltar ao início')


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

    def test_superusuario_com_papel_operador_pode_excluir(self):
        dono = User.objects.create_superuser('dono', password='senha-teste-123')
        Perfil.objects.create(usuario=dono, organizacao=self.org_a, papel=Perfil.OPERADOR)
        self.client.force_login(dono)
        self.assertContains(self.client.get(reverse('lista')), 'Excluir')
        url = reverse('excluir_livro', args=[self.livro_a.pk])
        self.assertRedirects(self.client.post(url), reverse('lista'))

    def test_operador_nao_pode_excluir_pela_api(self):
        self.client.force_login(self.operador_a)
        resposta = self.client.delete(f'/api/livros/{self.livro_a.pk}/')
        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(Livro.objects.filter(pk=self.livro_a.pk).exists())

    def test_admin_pode_excluir_pela_api(self):
        resposta = self.client.delete(f'/api/livros/{self.livro_a.pk}/')
        self.assertEqual(resposta.status_code, 204)


class DonoDoLivroTests(IsolamentoBase):
    def livro_do_operador(self):
        return Livro.objects.create(
            organizacao=self.org_a, titulo='Livro do Otto',
            autor=self.autor_a, ano=2001, cadastrado_por=self.operador_a,
        )

    def test_cadastrar_livro_guarda_quem_cadastrou(self):
        self.client.force_login(self.operador_a)
        self.client.post(reverse('novo_livro'), self.dados_livro())
        livro = Livro.objects.get(titulo='Livro Novo')
        self.assertEqual(livro.cadastrado_por, self.operador_a)

    def test_quem_cadastrou_pode_editar(self):
        livro = self.livro_do_operador()
        self.client.force_login(self.operador_a)
        url = reverse('editar_livro', args=[livro.pk])
        resposta = self.client.post(url, self.dados_livro(titulo='Livro do Otto (2a ed.)'))
        self.assertRedirects(resposta, reverse('lista'))
        livro.refresh_from_db()
        self.assertEqual(livro.titulo, 'Livro do Otto (2a ed.)')
        self.assertEqual(livro.cadastrado_por, self.operador_a)

    def test_quem_cadastrou_pode_excluir(self):
        livro = self.livro_do_operador()
        self.client.force_login(self.operador_a)
        url = reverse('excluir_livro', args=[livro.pk])
        self.assertRedirects(self.client.post(url), reverse('lista'))
        self.assertFalse(Livro.objects.filter(pk=livro.pk).exists())

    def test_operador_nao_pode_editar_livro_de_outra_pessoa(self):
        self.client.force_login(self.operador_a)
        url = reverse('editar_livro', args=[self.livro_a.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, self.dados_livro()).status_code, 403)

    def test_admin_pode_editar_livro_de_qualquer_pessoa(self):
        livro = self.livro_do_operador()
        url = reverse('editar_livro', args=[livro.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_lista_mostra_botoes_so_nos_livros_proprios(self):
        livro = self.livro_do_operador()
        self.client.force_login(self.operador_a)
        resposta = self.client.get(reverse('lista'))
        self.assertContains(resposta, reverse('excluir_livro', args=[livro.pk]))
        self.assertNotContains(resposta, reverse('excluir_livro', args=[self.livro_a.pk]))
        self.assertNotContains(resposta, reverse('editar_livro', args=[self.livro_a.pk]))

    def test_api_criar_guarda_quem_cadastrou(self):
        self.client.force_login(self.operador_a)
        resposta = self.client.post('/api/livros/', self.dados_livro(), content_type='application/json')
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()['cadastrado_por'], 'otto')

    def test_api_quem_cadastrou_pode_excluir(self):
        livro = self.livro_do_operador()
        self.client.force_login(self.operador_a)
        self.assertEqual(self.client.delete(f'/api/livros/{livro.pk}/').status_code, 204)

    def test_api_operador_nao_pode_editar_livro_de_outra_pessoa(self):
        self.client.force_login(self.operador_a)
        resposta = self.client.patch(
            f'/api/livros/{self.livro_a.pk}/', {'titulo': 'Mudado'}, content_type='application/json',
        )
        self.assertEqual(resposta.status_code, 403)
        self.livro_a.refresh_from_db()
        self.assertEqual(self.livro_a.titulo, 'Dom Casmurro')


class MensagensTests(IsolamentoBase):
    def mensagens(self, resposta):
        return [str(m) for m in get_messages(resposta.wsgi_request)]

    def test_cadastrar_livro_mostra_mensagem(self):
        resposta = self.client.post(reverse('novo_livro'), self.dados_livro())
        self.assertIn('Livro "Livro Novo" cadastrado.', self.mensagens(resposta))

    def test_editar_livro_mostra_mensagem(self):
        url = reverse('editar_livro', args=[self.livro_a.pk])
        resposta = self.client.post(url, self.dados_livro(titulo='Dom Casmurro'))
        self.assertIn('Livro "Dom Casmurro" atualizado.', self.mensagens(resposta))

    def test_excluir_livro_mostra_mensagem(self):
        url = reverse('excluir_livro', args=[self.livro_a.pk])
        resposta = self.client.post(url)
        self.assertIn('Livro "Dom Casmurro" excluído.', self.mensagens(resposta))

    def test_cadastrar_autor_mostra_mensagem(self):
        resposta = self.client.post(reverse('autores'), {'nome': 'Clarice Lispector'})
        self.assertIn('Autor "Clarice Lispector" cadastrado.', self.mensagens(resposta))

    def test_mensagem_aparece_na_pagina_seguinte(self):
        resposta = self.client.post(reverse('novo_livro'), self.dados_livro(), follow=True)
        self.assertContains(resposta, 'class="mensagem mensagem-success"')


class AnoTests(IsolamentoBase):
    def test_ano_antes_de_1000_da_erro(self):
        resposta = self.client.post(reverse('novo_livro'), self.dados_livro(ano=999))
        self.assertIn('ano', resposta.context['form'].errors)
        self.assertFalse(Livro.objects.filter(titulo='Livro Novo').exists())

    def test_ano_no_futuro_da_erro(self):
        ano_que_vem = timezone.now().year + 1
        resposta = self.client.post(reverse('novo_livro'), self.dados_livro(ano=ano_que_vem))
        self.assertIn('ano', resposta.context['form'].errors)

    def test_ano_atual_e_aceito(self):
        resposta = self.client.post(reverse('novo_livro'), self.dados_livro(ano=timezone.now().year))
        self.assertRedirects(resposta, reverse('lista'))

    def test_api_recusa_ano_no_futuro(self):
        resposta = self.client.post(
            '/api/livros/', self.dados_livro(ano=timezone.now().year + 1),
            content_type='application/json',
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('ano', resposta.json())


class PaginasDeErroTests(IsolamentoBase):
    def test_403_usa_a_pagina_do_sistema(self):
        sem_perfil = User.objects.create_user('carlos', password='senha-teste-123')
        self.client.force_login(sem_perfil)
        resposta = self.client.get(reverse('lista'))
        self.assertEqual(resposta.status_code, 403)
        self.assertContains(resposta, 'Acesso negado', status_code=403)
        self.assertContains(resposta, 'não está ligado a nenhuma organização', status_code=403)

    def test_404_usa_a_pagina_do_sistema(self):
        resposta = self.client.get(reverse('editar_livro', args=[999999]))
        self.assertContains(resposta, 'Página não encontrada', status_code=404)


class PaginacaoTests(IsolamentoBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Livro.objects.bulk_create([
            Livro(organizacao=cls.org_a, titulo=f'Livro {n:02d}', autor=cls.autor_a, ano=2000)
            for n in range(1, 26)
        ])

    def test_primeira_pagina_tem_20_livros(self):
        resposta = self.client.get(reverse('lista'))
        self.assertEqual(len(resposta.context['livros']), 20)
        self.assertEqual(resposta.context['pagina'].paginator.num_pages, 2)

    def test_segunda_pagina_tem_o_resto(self):
        resposta = self.client.get(reverse('lista'), {'pagina': 2})
        self.assertEqual(len(resposta.context['livros']), 6)

    def test_pagina_invalida_mostra_a_primeira(self):
        resposta = self.client.get(reverse('lista'), {'pagina': 'abc'})
        self.assertEqual(resposta.context['pagina'].number, 1)

    def test_links_da_paginacao_mantem_os_filtros(self):
        resposta = self.client.get(reverse('lista'), {'nome': 'Livro'})
        self.assertContains(resposta, '?nome=Livro&pagina=2')


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


def em(ano, mes, dia=15):
    return timezone.make_aware(datetime(ano, mes, dia, 12, 0))


class DashboardBase(IsolamentoBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.clarice = Autor.objects.create(organizacao=cls.org_a, nome='Clarice Lispector')
        Livro.objects.filter(pk=cls.livro_a.pk).update(cadastrado_em=em(2026, 1))
        Livro.objects.create(
            organizacao=cls.org_a, titulo='A Hora da Estrela', autor=cls.clarice,
            ano=1977, categoria='800', cadastrado_em=em(2026, 3),
        )
        Livro.objects.create(
            organizacao=cls.org_a, titulo='Memórias Póstumas', autor=cls.autor_a,
            ano=1881, categoria='800', disponivel=False, cadastrado_em=em(2026, 3),
        )
        for n in range(4):
            Livro.objects.create(
                organizacao=cls.org_b, titulo=f'Livro B {n}', autor=cls.autor_b,
                ano=1900, cadastrado_em=em(2026, 2),
            )


class DashboardTests(DashboardBase):
    def test_indicadores_so_da_propria_organizacao(self):
        resposta = self.client.get(reverse('dashboard'))
        self.assertEqual(resposta.context['indicadores'], {
            'total': 3, 'disponiveis': 2, 'indisponiveis': 1, 'autores': 2,
        })

    def test_outra_organizacao_ve_os_proprios_numeros(self):
        self.client.force_login(self.user_b)
        resposta = self.client.get(reverse('dashboard'))
        self.assertEqual(resposta.context['indicadores']['total'], 5)

    def test_ranking_de_autores(self):
        resposta = self.client.get(reverse('dashboard'))
        self.assertEqual(resposta.context['ranking'], [
            {'autor__nome': 'Machado de Assis', 'total': 2},
            {'autor__nome': 'Clarice Lispector', 'total': 1},
        ])

    def test_livros_por_mes_em_ordem(self):
        resposta = self.client.get(reverse('dashboard'))
        self.assertEqual(resposta.context['por_mes'], [
            {'mes': '01/2026', 'total': 1},
            {'mes': '03/2026', 'total': 2},
        ])

    def test_livros_por_categoria_com_nome(self):
        resposta = self.client.get(reverse('dashboard'))
        self.assertEqual(resposta.context['por_categoria'], [
            {'categoria': '000 – Generalidades e Informação', 'total': 1},
            {'categoria': '800 – Literatura', 'total': 2},
        ])

    def test_filtro_por_periodo(self):
        resposta = self.client.get(reverse('dashboard'), {'inicio': '2026-03-01', 'fim': '2026-03-31'})
        self.assertEqual(resposta.context['indicadores']['total'], 2)
        self.assertEqual(resposta.context['por_mes'], [{'mes': '03/2026', 'total': 2}])

    def test_data_invalida_nao_quebra_e_ignora_o_filtro(self):
        resposta = self.client.get(reverse('dashboard'), {'inicio': 'abc'})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['indicadores']['total'], 3)
        self.assertContains(resposta, 'O filtro foi ignorado.')

    def test_inicio_depois_do_fim_mostra_erro(self):
        resposta = self.client.get(reverse('dashboard'), {'inicio': '2026-05-01', 'fim': '2026-01-01'})
        self.assertContains(resposta, 'não pode ser depois da data de fim')

    def test_dashboard_vazio_nao_da_erro(self):
        org_c = Organizacao.objects.create(nome='Biblioteca C')
        carla = User.objects.create_user('carla', password='senha-teste-123')
        Perfil.objects.create(usuario=carla, organizacao=org_c, papel=Perfil.ADMIN)
        self.client.force_login(carla)
        resposta = self.client.get(reverse('dashboard'))
        self.assertEqual(resposta.context['indicadores']['total'], 0)
        self.assertContains(resposta, 'Sem dados no período.')

    def test_operador_nao_ve_serie_nem_exportacao(self):
        self.client.force_login(self.operador_a)
        resposta = self.client.get(reverse('dashboard'))
        self.assertFalse(resposta.context['mostra_series'])
        self.assertNotIn('por_mes', resposta.context)
        self.assertNotContains(resposta, 'Exportar CSV')
        self.assertEqual(resposta.context['indicadores']['total'], 3)

    def test_sem_login_redireciona(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)


class ExportarCsvTests(DashboardBase):
    def conteudo(self, resposta):
        return resposta.content.decode('utf-8-sig')

    def test_admin_baixa_csv_so_da_propria_organizacao(self):
        resposta = self.client.get(reverse('exportar_csv'))
        self.assertEqual(resposta['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', resposta['Content-Disposition'])
        texto = self.conteudo(resposta)
        self.assertIn('Título;Autor;Ano', texto)
        self.assertIn('Dom Casmurro', texto)
        self.assertNotIn('Livro B', texto)
        self.assertEqual(len(texto.strip().splitlines()), 4)

    def test_csv_respeita_o_periodo(self):
        resposta = self.client.get(reverse('exportar_csv'), {'inicio': '2026-03-01'})
        texto = self.conteudo(resposta)
        self.assertNotIn('Dom Casmurro', texto)
        self.assertIn('A Hora da Estrela', texto)

    def test_csv_neutraliza_formulas(self):
        Livro.objects.create(
            organizacao=self.org_a, titulo='=1+1', autor=self.autor_a, ano=2000,
        )
        texto = self.conteudo(self.client.get(reverse('exportar_csv')))
        self.assertIn("'=1+1", texto)

    def test_operador_nao_exporta(self):
        self.client.force_login(self.operador_a)
        self.assertEqual(self.client.get(reverse('exportar_csv')).status_code, 403)


class DashboardApiTests(DashboardBase):
    def test_api_devolve_as_metricas_da_organizacao(self):
        dados = self.client.get('/api/dashboard/').json()
        self.assertEqual(dados['indicadores']['total'], 3)
        self.assertIn('por_mes', dados)

    def test_api_do_operador_nao_tem_serie(self):
        self.client.force_login(self.operador_a)
        dados = self.client.get('/api/dashboard/').json()
        self.assertNotIn('por_mes', dados)

    def test_api_recusa_data_invalida(self):
        resposta = self.client.get('/api/dashboard/', {'inicio': 'abc'})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('inicio', resposta.json())

    def test_api_sem_login_e_bloqueada(self):
        self.client.logout()
        self.assertIn(self.client.get('/api/dashboard/').status_code, (401, 403))


class ConsultasTests(IsolamentoBase):
    def contar_consultas(self, url):
        with CaptureQueriesContext(connection) as contexto:
            self.client.get(url)
        return len(contexto)

    def criar_livros(self, quantidade, inicio):
        for n in range(inicio, inicio + quantidade):
            Livro.objects.create(
                organizacao=self.org_a, titulo=f'Livro {n:03d}', autor=self.autor_a,
                ano=2000, cadastrado_por=self.user_a,
            )

    def assert_nao_cresce_com_mais_livros(self, url):
        self.criar_livros(3, 0)
        antes = self.contar_consultas(url)
        self.criar_livros(10, 100)
        depois = self.contar_consultas(url)
        self.assertEqual(antes, depois, f'{url}: {antes} consultas com 4 livros, {depois} com 14')

    def test_lista_de_livros_sem_n_mais_1(self):
        self.assert_nao_cresce_com_mais_livros(reverse('lista'))

    def test_dashboard_sem_n_mais_1(self):
        self.assert_nao_cresce_com_mais_livros(reverse('dashboard'))

    def test_csv_sem_n_mais_1(self):
        self.assert_nao_cresce_com_mais_livros(reverse('exportar_csv'))

    def test_api_de_livros_sem_n_mais_1(self):
        self.assert_nao_cresce_com_mais_livros('/api/livros/')

    def test_csv_usa_select_related(self):
        self.criar_livros(5, 0)
        with self.assertNumQueries(1):
            livros = (
                Livro.objects.filter(organizacao=self.org_a, cadastrado_por=self.user_a)
                .select_related('autor', 'cadastrado_por')
            )
            for livro in livros:
                livro.autor.nome, livro.cadastrado_por.username
