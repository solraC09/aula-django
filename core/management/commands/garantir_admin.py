import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from core.models import Perfil
from core.utils import biblioteca_principal, usuario_admin_fixo


class Command(BaseCommand):
    help = "Cria ou atualiza o administrador fixo do sistema a partir do .env."

    def handle(self, *args, **options):
        usuario = usuario_admin_fixo()
        senha = os.environ.get("ADMIN_SENHA", "")
        if not usuario or not senha:
            raise CommandError("Defina ADMIN_USUARIO e ADMIN_SENHA no arquivo .env.")

        User = get_user_model()
        admin, criado = User.objects.get_or_create(username=usuario)
        admin.email = os.environ.get("ADMIN_EMAIL", admin.email)
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(senha)
        admin.save()

        org = biblioteca_principal()
        Perfil.objects.update_or_create(
            usuario=admin,
            defaults={"organizacao": org, "papel": Perfil.ADMIN},
        )

        acao = "criado" if criado else "atualizado"
        self.stdout.write(self.style.SUCCESS(
            f"Administrador '{usuario}' {acao} na biblioteca '{org}'."
        ))
