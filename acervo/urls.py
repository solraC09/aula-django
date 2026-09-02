from django.urls import path
from . import views


urlpatterns = [
    path('', views.inicio),
]

urlpatterns = [
    path(
    'livros/',
    views.lista_livros,
    name='lista'
    ),
]
