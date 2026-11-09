from rest_framework.permissions import BasePermission

from .utils import perfil_atual


class SomenteAdminExclui(BasePermission):
    message = "Apenas administradores podem excluir."

    def has_permission(self, request, view):
        if request.method != "DELETE":
            return True
        return perfil_atual(request).eh_admin
