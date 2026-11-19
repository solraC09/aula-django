from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from core.permissions import DonoOuAdmin
from core.utils import org_atual

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
