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
        repetido = (
            Autor.objects.filter(organizacao=self.org, nome__iexact=nome)
            .exclude(pk=self.instance.pk)
            .exists()
        )
        if repetido:
            raise forms.ValidationError('Já existe um autor com esse nome.')
        return nome


class PeriodoForm(forms.Form):
    inicio = forms.DateField(
        label='Início', required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    fim = forms.DateField(
        label='Fim', required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def clean(self):
        dados = super().clean()
        inicio, fim = dados.get('inicio'), dados.get('fim')
        if inicio and fim and inicio > fim:
            raise forms.ValidationError('A data de início não pode ser depois da data de fim.')
        return dados
