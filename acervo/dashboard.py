from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

from .forms import PeriodoForm
from .models import Livro

CATEGORIAS = dict(Livro.CATEGORIA_CHOICES)


def livros_da_organizacao(org):
    return Livro.objects.filter(organizacao=org)


def filtrar_periodo(params, qs):
    form = PeriodoForm(params)
    if form.is_valid():
        if form.cleaned_data['inicio']:
            qs = qs.filter(cadastrado_em__date__gte=form.cleaned_data['inicio'])
        if form.cleaned_data['fim']:
            qs = qs.filter(cadastrado_em__date__lte=form.cleaned_data['fim'])
    return form, qs


def indicadores(base):
    return base.aggregate(
        total=Count('id'),
        disponiveis=Count('id', filter=Q(disponivel=True)),
        indisponiveis=Count('id', filter=Q(disponivel=False)),
        autores=Count('autor', distinct=True),
    )


def ranking_autores(base, limite=5):
    return list(
        base.values('autor__nome')
        .annotate(total=Count('id'))
        .order_by('-total', 'autor__nome')[:limite]
    )


def livros_por_mes(base):
    linhas = (
        base.annotate(mes=TruncMonth('cadastrado_em'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    return [{'mes': linha['mes'].strftime('%m/%Y'), 'total': linha['total']} for linha in linhas]


def livros_por_categoria(base):
    linhas = base.values('categoria').annotate(total=Count('id')).order_by('categoria')
    return [
        {'categoria': CATEGORIAS.get(linha['categoria'], linha['categoria']), 'total': linha['total']}
        for linha in linhas
    ]


def montar_dashboard(base, com_series):
    dados = {
        'indicadores': indicadores(base),
        'ranking': ranking_autores(base),
        'por_categoria': livros_por_categoria(base),
    }
    if com_series:
        dados['por_mes'] = livros_por_mes(base)
    return dados
