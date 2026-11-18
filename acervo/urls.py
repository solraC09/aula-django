from django.urls import path

from . import views


urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('livros/', views.lista_livros, name='lista'),
    path('livros/novo/', views.novo_livro, name='novo_livro'),
    path('livros/<int:pk>/editar/', views.editar_livro, name='editar_livro'),
    path('livros/<int:pk>/excluir/', views.excluir_livro, name='excluir_livro'),
    path('autores/', views.autores, name='autores'),
    path('autores/<int:pk>/editar/', views.editar_autor, name='editar_autor'),
    path('autores/<int:pk>/excluir/', views.excluir_autor, name='excluir_autor'),
]
