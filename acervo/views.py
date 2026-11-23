import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from core.utils import exigir_admin, org_atual, perfil_atual

from .dashboard import filtrar_periodo, livros_da_organizacao, montar_dashboard

from .forms import AutorForm, LivroForm
from .models import Autor, Livro

LIVROS_POR_PAGINA = 20


@login_required
def inicio(request):
    org = org_atual(request)
    total = Livro.objects.filter(organizacao=org).count()
    return render(request, 'acervo/inicio.html', {
        'organizacao': org,
        'total_livros': total,
    })


@login_required
def lista_livros(request):
    org = org_atual(request)
    livros = (
        Livro.objects.filter(organizacao=org)
        .select_related('autor', 'cadastrado_por')
        .order_by('titulo')
    )

    nome = request.GET.get('nome', '')
    tipo = request.GET.get('tipo', '')
    categoria = request.GET.get('categoria', '')

    if nome:
        livros = livros.filter(titulo__icontains=nome)
    if tipo:
        livros = livros.filter(tipo=tipo)
    if categoria:
        livros = livros.filter(categoria=categoria)

    pagina = Paginator(livros, LIVROS_POR_PAGINA).get_page(request.GET.get('pagina'))
    for livro in pagina:
        livro.pode_alterar = livro.pode_ser_alterado_por(request.user)

    filtros = request.GET.copy()
    filtros.pop('pagina', None)

    return render(request, 'acervo/lista.html', {
        'livros': pagina,
        'pagina': pagina,
        'filtros': filtros.urlencode(),
        'tipos': Livro.TIPO_CHOICES,
        'categorias': Livro.CATEGORIA_CHOICES,
        'filtro_nome': nome,
        'filtro_tipo': tipo,
        'filtro_categoria': categoria,
    })


@login_required
def novo_livro(request):
    org = org_atual(request)
    form = LivroForm(request.POST or None, org=org)

    if request.method == 'POST' and form.is_valid():
        livro = form.save(commit=False)
        livro.organizacao = org
        livro.cadastrado_por = request.user
        livro.save()
        messages.success(request, f'Livro "{livro.titulo}" cadastrado.')
        return redirect('lista')

    return render(request, 'acervo/form.html', {
        'form': form,
        'titulo_pagina': 'Cadastrar livro',
    })


def buscar_livro_alteravel(request, pk, org):
    livro = get_object_or_404(Livro, pk=pk, organizacao=org)
    if not livro.pode_ser_alterado_por(request.user):
        raise PermissionDenied('Só quem cadastrou o livro ou um administrador pode alterá-lo.')
    return livro


@login_required
def editar_livro(request, pk):
    org = org_atual(request)
    livro = buscar_livro_alteravel(request, pk, org)
    form = LivroForm(request.POST or None, instance=livro, org=org)

    if request.method == 'POST' and form.is_valid():
        livro = form.save()
        messages.success(request, f'Livro "{livro.titulo}" atualizado.')
        return redirect('lista')

    return render(request, 'acervo/form.html', {
        'form': form,
        'titulo_pagina': 'Editar livro',
    })


@login_required
def excluir_livro(request, pk):
    livro = buscar_livro_alteravel(request, pk, org_atual(request))

    if request.method == 'POST':
        titulo = livro.titulo
        livro.delete()
        messages.success(request, f'Livro "{titulo}" excluído.')
        return redirect('lista')

    return render(request, 'acervo/confirmar_exclusao.html', {'livro': livro})


def endereco_de_volta(request, padrao):
    destino = request.GET.get('next', '')
    if url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino
    return reverse(padrao)


@login_required
def autores(request):
    org = org_atual(request)
    form = AutorForm(request.POST or None, org=org)

    if request.method == 'POST' and form.is_valid():
        autor = form.save(commit=False)
        autor.organizacao = org
        autor.save()
        messages.success(request, f'Autor "{autor.nome}" cadastrado.')
        return redirect(request.get_full_path())

    return render(request, 'acervo/autores.html', {
        'autores': Autor.objects.filter(organizacao=org).annotate(total_livros=Count('livro')),
        'form': form,
        'voltar_para': endereco_de_volta(request, 'lista'),
    })


@login_required
def editar_autor(request, pk):
    org = org_atual(request)
    autor = get_object_or_404(Autor, pk=pk, organizacao=org)
    form = AutorForm(request.POST or None, instance=autor, org=org)

    if request.method == 'POST' and form.is_valid():
        autor = form.save()
        messages.success(request, f'Autor "{autor.nome}" atualizado.')
        return redirect('autores')

    return render(request, 'acervo/autor_form.html', {'form': form})


@login_required
def excluir_autor(request, pk):
    exigir_admin(request)
    autor = get_object_or_404(Autor, pk=pk, organizacao=org_atual(request))
    total_livros = autor.livro_set.count()

    if request.method == 'POST' and total_livros == 0:
        nome = autor.nome
        autor.delete()
        messages.success(request, f'Autor "{nome}" excluído.')
        return redirect('autores')

    return render(request, 'acervo/confirmar_exclusao_autor.html', {
        'autor': autor,
        'total_livros': total_livros,
    })


@login_required
def dashboard(request):
    org = org_atual(request)
    eh_admin = perfil_atual(request).eh_admin
    form, base = filtrar_periodo(request.GET, livros_da_organizacao(org))

    contexto = montar_dashboard(base, com_series=eh_admin)
    contexto.update({
        'organizacao': org,
        'form': form,
        'mostra_series': eh_admin,
        'filtros': request.GET.urlencode(),
    })
    return render(request, 'acervo/dashboard.html', contexto)


def celula_segura(valor):
    texto = '' if valor is None else str(valor)
    if texto[:1] in ('=', '+', '-', '@'):
        return "'" + texto
    return texto


@login_required
def exportar_csv(request):
    exigir_admin(request)
    org = org_atual(request)
    _, livros = filtrar_periodo(request.GET, livros_da_organizacao(org))
    livros = livros.select_related('autor', 'cadastrado_por').order_by('titulo')

    resposta = HttpResponse(content_type='text/csv; charset=utf-8')
    resposta['Content-Disposition'] = 'attachment; filename="livros.csv"'
    resposta.write('\ufeff')

    escritor = csv.writer(resposta, delimiter=';')
    escritor.writerow([
        'Título', 'Autor', 'Ano', 'Tipo', 'Categoria',
        'Disponível', 'Cadastrado por', 'Cadastrado em',
    ])
    for livro in livros:
        escritor.writerow([celula_segura(valor) for valor in [
            livro.titulo,
            livro.autor.nome,
            livro.ano,
            livro.get_tipo_display(),
            livro.get_categoria_display(),
            'Sim' if livro.disponivel else 'Não',
            livro.cadastrado_por.username if livro.cadastrado_por else '',
            timezone.localtime(livro.cadastrado_em).strftime('%d/%m/%Y %H:%M'),
        ]])
    return resposta
