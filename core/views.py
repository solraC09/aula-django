from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import CadastroForm
from .models import Perfil
from .utils import biblioteca_principal


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("inicio")

    form = CadastroForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            usuario = form.save()
            Perfil.objects.create(
                usuario=usuario,
                organizacao=biblioteca_principal(),
                papel=Perfil.OPERADOR,
            )
        login(request, usuario)
        messages.success(request, f"Conta criada. Bem-vindo(a), {usuario.username}!")
        return redirect("inicio")

    return render(request, "registration/cadastro.html", {"form": form})
