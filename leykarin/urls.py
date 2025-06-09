"""
URL configuration for leykarin project - ACTUALIZADO CON VALIDACIÓN DE RUT
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from appkarin import views
from appkarin.service import (
    ServiceLoginAdminAPIView,
    ServiceLogoutAdminAPIView, 
    ServiceCheckAuthAdminAPIView,
    ServiceItemsAPIView,
    ServiceProcessDenunciaAPIView,
    ServiceUserDenunciaAPIView,
    DenunciaWizardDataAPIView,
    ConsultaDenunciaAPIView,
    ValidateRutAPIView,              # ⭐ NUEVA API
    AutocompleteUserDataAPIView,   # ⭐ NUEVA API
    CambiarEstadoDenunciaAPIView,
    DenunciaDetalleAPIView,
    DenunciaMensajeAPIView,
    DenunciaInfoAPIView,
    DescargarDenunciaAPIView
)

from appkarin.service_datatable import (
    SimpleDenunciaDataTableAPIView,
)


urlpatterns = [
    
    # 🔐 RUTAS DE AUTENTICACIÓN ADMIN
    path('api/admin/login/', ServiceLoginAdminAPIView.as_view(), name='admin_login_api'),
    path('api/admin/logout/', ServiceLogoutAdminAPIView.as_view(), name='admin_logout_api'),
    path('api/admin/check-auth/', ServiceCheckAuthAdminAPIView.as_view(), name='admin_check_auth_api'),




    # =================================================================
    # APIs CON LAS MISMAS URLs EXACTAS (Corregidas para evitar 404)
    # =================================================================
    
    # ✅ URLs EXACTAS del service.py original - Agregando csrf_exempt
    path('api/create/denuncia/items/', 
         csrf_exempt(ServiceItemsAPIView.as_view()), 
         name='process_items'),
    
    path('api/create/denuncia/wizzard/', 
         csrf_exempt(ServiceProcessDenunciaAPIView.as_view()), 
         name='process_denuncia'),
    
    path('api/create/denuncia/user/', 
         csrf_exempt(ServiceUserDenunciaAPIView.as_view()), 
         name='process_user'),

    # =================================================================
    # 🆕 NUEVAS APIs PARA VALIDACIÓN DE RUT
    # =================================================================
    
    # ⭐ API para validar RUT en tiempo real
    path('api/validate/rut/', 
         csrf_exempt(ValidateRutAPIView.as_view()), 
         name='validate_rut'),
    
    # ⭐ API para autocompletar datos de usuario
    path('api/autocomplete/user/', 
         csrf_exempt(AutocompleteUserDataAPIView.as_view()), 
         name='autocomplete_user'),

    # 🆕 APIs adicionales funcionales
    path('api/wizard/data/', 
         DenunciaWizardDataAPIView.as_view(), 
         name='wizard_data'),
    
    path('api/dashboard/denuncia/', 
         csrf_exempt(ConsultaDenunciaAPIView.as_view()), 
         name='consulta_denuncia'),



     path('api/cambiar-estado-denuncia/', CambiarEstadoDenunciaAPIView.as_view()),
     path('api/denuncia-detalle/<str:codigo>/', DenunciaDetalleAPIView.as_view()),
     path('api/denuncia-mensaje/<str:codigo>/', DenunciaMensajeAPIView.as_view()),
     path('api/denuncia-info/<str:codigo>/', DenunciaInfoAPIView.as_view()),
     path('api/descargar-denuncia/<str:codigo>/', DescargarDenunciaAPIView.as_view()),



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
    path('admin/login/', views.renderLoginAdmin, name='login'),

    # =================================================================
    # VISTAS PARA RENDERIZAR Y GENERAR DATATABLES (Sin cambios)
    # =================================================================
     path('api/datatable/denuncias/simple/', 
         csrf_exempt(SimpleDenunciaDataTableAPIView.as_view()), 
         name='datatable_simple'),
     
     path('denuncias/consulta/', 
         views.renderConsultaDenuncia, 
         name='consulta_denuncias'),


    # =================================================================
    # DJANGO ADMIN
    # =================================================================
    path(settings.ADMIN_URL, admin.site.urls),
]