from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Organizacao, Perfil
from .utils import usuario_admin_fixo

User = get_user_model()
admin.site.unregister(User)


def eh_admin_fixo(usuario):
    return bool(usuario_admin_fixo()) and usuario.username == usuario_admin_fixo()


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    def has_delete_permission(self, request, obj=None):
        if obj is not None and eh_admin_fixo(obj):
            return False
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset.exclude(username=usuario_admin_fixo()))


@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "criada_em")
    search_fields = ("nome",)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "organizacao", "papel")
    list_filter = ("organizacao", "papel")
