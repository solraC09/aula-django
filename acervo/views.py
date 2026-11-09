from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.utils import exigir_admin, org_atual

from .forms import AutorForm, LivroForm
from .models import Autor, Livro


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
        .select_related('autor')
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

    return render(request, 'acervo/lista.html', {
        'livros': livros,
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
        livro.save()
        return redirect('lista')

    return render(request, 'acervo/form.html', {
        'form': form,
        'titulo_pagina': 'Cadastrar livro',
    })


@login_required
def editar_livro(request, pk):
    org = org_atual(request)
    livro = get_object_or_404(Livro, pk=pk, organizacao=org)
    form = LivroForm(request.POST or None, instance=livro, org=org)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('lista')

    return render(request, 'acervo/form.html', {
        'form': form,
        'titulo_pagina': 'Editar livro',
    })


@login_required
def excluir_livro(request, pk):
    exigir_admin(request)
    livro = get_object_or_404(Livro, pk=pk, organizacao=org_atual(request))

    if request.method == 'POST':
        livro.delete()
        return redirect('lista')

    return render(request, 'acervo/confirmar_exclusao.html', {'livro': livro})


@login_required
def autores(request):
    org = org_atual(request)
    form = AutorForm(request.POST or None, org=org)

    if request.method == 'POST' and form.is_valid():
        autor = form.save(commit=False)
        autor.organizacao = org
        autor.save()
        return redirect('autores')

    return render(request, 'acervo/autores.html', {
        'autores': Autor.objects.filter(organizacao=org),
        'form': form,
    })
