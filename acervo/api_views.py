from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from core.permissions import SomenteAdminExclui
from core.utils import org_atual

from .models import Livro
from .serializers import LivroSerializer


class DaOrganizacaoMixin:
    permission_classes = [IsAuthenticated, SomenteAdminExclui]

    def get_queryset(self):
        return (
            Livro.objects.filter(organizacao=org_atual(self.request))
            .select_related('autor')
            .order_by('titulo')
        )


class LivroListCreate(DaOrganizacaoMixin, generics.ListCreateAPIView):
    serializer_class = LivroSerializer

    def perform_create(self, serializer):
        serializer.save(organizacao=org_atual(self.request))


class LivroDetail(DaOrganizacaoMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LivroSerializer
