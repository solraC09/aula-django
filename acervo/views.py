from django.shortcuts import render
from django.http import HttpResponse
from .models import Livro


def inicio(request):
    return HttpResponse(
        'Olá, acervo!'
    )
    
def lista_livros(request):
    livros = Livro.objects.all() # busca no banco
    return render(
    request, 'acervo/lista.html',
    {'livros': livros} # envia ao template
)

