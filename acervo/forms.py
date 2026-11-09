from django import forms

from .models import Autor, Livro


class LivroForm(forms.ModelForm):
    class Meta:
        model = Livro
        fields = ['titulo', 'autor', 'ano', 'tipo', 'categoria', 'disponivel']

    def __init__(self, *args, org=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['autor'].queryset = Autor.objects.filter(organizacao=org)


class AutorForm(forms.ModelForm):
    class Meta:
        model = Autor
        fields = ['nome']

    def __init__(self, *args, org=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.org = org

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()
        if Autor.objects.filter(organizacao=self.org, nome__iexact=nome).exists():
            raise forms.ValidationError('Já existe um autor com esse nome.')
        return nome
