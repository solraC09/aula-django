from django.urls import path

from .api_views import DashboardApi, LivroDetail, LivroListCreate


urlpatterns = [
    path('livros/', LivroListCreate.as_view(), name='api_livros'),
    path('livros/<int:pk>/', LivroDetail.as_view(), name='api_livro_detalhe'),
    path('dashboard/', DashboardApi.as_view(), name='api_dashboard'),
]
