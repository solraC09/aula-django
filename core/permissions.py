from rest_framework.permissions import SAFE_METHODS, BasePermission


class DonoOuAdmin(BasePermission):
    message = "Só quem cadastrou o livro ou um administrador pode alterá-lo."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.pode_ser_alterado_por(request.user)
