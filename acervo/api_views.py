from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import DonoOuAdmin
from core.utils import org_atual, perfil_atual

from .dashboard import filtrar_periodo, livros_da_organizacao, montar_dashboard

from .models import Livro
from .serializers import LivroSerializer


class DaOrganizacaoMixin:
    permission_classes = [IsAuthenticated, DonoOuAdmin]

    def get_queryset(self):
        return (
            Livro.objects.filter(organizacao=org_atual(self.request))
            .select_related('autor', 'cadastrado_por')
            .order_by('titulo')
        )


class LivroListCreate(DaOrganizacaoMixin, generics.ListCreateAPIView):
    serializer_class = LivroSerializer

    def perform_create(self, serializer):
        serializer.save(
            organizacao=org_atual(self.request),
            cadastrado_por=self.request.user,
        )


class LivroDetail(DaOrganizacaoMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LivroSerializer


class DashboardApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = org_atual(request)
        form, base = filtrar_periodo(request.query_params, livros_da_organizacao(org))
        if not form.is_valid():
            return Response(form.errors, status=400)
        return Response(montar_dashboard(base, com_series=perfil_atual(request).eh_admin))
