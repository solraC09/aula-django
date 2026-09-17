from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Livro
from .forms import LivroForm


def inicio(request):
    return render(request, 'acervo/inicio.html')


def lista_livros(request):
    livros = Livro.objects.all()

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

def novo_livro(request):
    if request.method == 'POST':
        form = LivroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista')
    else:
        form = LivroForm()

    return render(request, 'acervo/form.html', {'form': form})