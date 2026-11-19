from rest_framework import serializers

from core.utils import org_atual

from .models import Livro


class LivroSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.nome', read_only=True)
    cadastrado_por = serializers.CharField(
        source='cadastrado_por.username', read_only=True, allow_null=True,
    )

    class Meta:
        model = Livro
        fields = [
            'id', 'titulo', 'autor', 'autor_nome', 'ano',
            'tipo', 'categoria', 'disponivel', 'cadastrado_por',
        ]

    def validate_autor(self, autor):
        if autor.organizacao != org_atual(self.context['request']):
            raise serializers.ValidationError('Autor não encontrado.')
        return autor
