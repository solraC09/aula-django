import os

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from .models import Organizacao


def perfil_atual(request):
    try:
        return request.user.perfil
    except ObjectDoesNotExist:
        raise PermissionDenied(
            "Seu usuário não está ligado a nenhuma organização. "
            "Peça a um administrador para criar o seu Perfil no Admin."
        )


def org_atual(request):
    return perfil_atual(request).organizacao


def exigir_admin(request):
    if not perfil_atual(request).eh_admin:
        raise PermissionDenied("Apenas administradores podem fazer isso.")


def biblioteca_principal():
    org = Organizacao.objects.order_by("pk").first()
    if org is None:
        org = Organizacao.objects.create(
            nome=os.environ.get("BIBLIOTECA_NOME", "Biblioteca"),
        )
    return org


def usuario_admin_fixo():
    return os.environ.get("ADMIN_USUARIO", "")
