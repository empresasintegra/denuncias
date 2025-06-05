"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path
from appkarin import views
from appkarin.views import (
    ServiceItemsAPIView,
    ServiceProcessDenunciaAPIView,
    ServiceUserDenunciaAPIView
)

urlpatterns = [
    # =================================================================
    # APIs CON LAS MISMAS URLs EXACTAS (No romper JavaScript)
    # =================================================================
    
    # ✅ URLs EXACTAS del service.py original - Solo cambian las views a APIView
    path('api/create/denuncia/items/', ServiceItemsAPIView.as_view(), name='process_items'),
    path('api/create/denuncia/wizzard/', ServiceProcessDenunciaAPIView.as_view(), name='process_denuncia'),
    path('api/create/denuncia/user/', ServiceUserDenunciaAPIView.as_view(), name='process_user'),

    # ⚠️ URLs comentadas del service.py original que no estaban implementadas
    # path('api/auth/admin/', service.serviceAdminAuth, name='auth'),
    # path('api/query/denunciaByCode', service.serviceDenunciaByCode, name='query_denuncia'),
    # path('api/query/denunciasByUser:', service.serviceDenunciaByUser, name='query_denuncia_by_user'),

    # =================================================================
    # VISTAS PARA RENDERIZAR TEMPLATES (Sin cambios)
    # =================================================================
    
    # Páginas principales
    path('', views.renderHome, name='home'),
    path('denuncia/Paso1/', views.renderItemsDenuncia, name='items'),
    path('denuncia/Paso2/', views.renderWizzDenuncia, name='denuncia_wizzard'),
    path('denuncia/Paso3/', views.renderUserDenuncia, name='user_register'),
    path('denuncia/final/', views.renderCodeDenuncia, name='code_view'),
    
    # Admin y consultas
    path('admin/login/', views.renderCodeDenuncia, name='login'),
    path('admin/consulta_denuncias/', views.renderConsultaDenuncia, name='denuncias_admin'),
    path('consulta_denuncias/', views.renderConsultaDenuncia, name='denuncias'),

    # =================================================================
    # DJANGO ADMIN
    # =================================================================
    path(settings.ADMIN_URL, admin.site.urls),
]