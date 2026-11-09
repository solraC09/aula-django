from rest_framework import serializers

from core.utils import org_atual

from .models import Livro


class LivroSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.nome', read_only=True)

    class Meta:
        model = Livro
        fields = [
            'id', 'titulo', 'autor', 'autor_nome', 'ano',
            'tipo', 'categoria', 'disponivel',
        ]

    def validate_autor(self, autor):
        if autor.organizacao != org_atual(self.context['request']):
            raise serializers.ValidationError('Autor não encontrado.')
        return autor
