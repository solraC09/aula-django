from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('contas/', include('django.contrib.auth.urls')),
    path('api/', include('acervo.api_urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', include('acervo.urls')),
]
