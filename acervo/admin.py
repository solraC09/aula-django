from django.contrib import admin

from .models import Autor, Livro


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'organizacao')
    list_filter = ('organizacao',)
    search_fields = ('nome',)


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'ano', 'tipo', 'categoria', 'disponivel', 'organizacao')
    list_filter = ('organizacao', 'tipo', 'categoria', 'disponivel')
    search_fields = ('titulo', 'autor__nome')
