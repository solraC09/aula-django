from django import forms
from django.contrib.auth.forms import UserCreationForm


class CadastroForm(UserCreationForm):
    email = forms.EmailField(label="E-mail", required=False)

    class Meta(UserCreationForm.Meta):
        fields = ("username", "email")
