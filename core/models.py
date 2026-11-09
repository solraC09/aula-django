from django.conf import settings
from django.db import models


class Organizacao(models.Model):
    nome = models.CharField(max_length=120)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Organização"
        verbose_name_plural = "Organizações"

    def __str__(self):
        return self.nome


class DaOrganizacao(models.Model):
    organizacao = models.ForeignKey(
        "core.Organizacao",
        on_delete=models.PROTECT,
    )

    class Meta:
        abstract = True


class Perfil(models.Model):
    ADMIN = "admin"
    OPERADOR = "operador"
    PAPEIS = [
        (ADMIN, "Administrador"),
        (OPERADOR, "Operador"),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    organizacao = models.ForeignKey(
        Organizacao,
        on_delete=models.PROTECT,
    )
    papel = models.CharField(
        max_length=20,
        choices=PAPEIS,
        default=OPERADOR,
    )

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return f"{self.usuario} ({self.organizacao})"

    @property
    def eh_admin(self):
        return self.papel == self.ADMIN
