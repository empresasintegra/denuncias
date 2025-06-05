"""
URL configuration for leykarin project - ACTUALIZADO CON VALIDACIÓN DE RUT
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from appkarin import views
from appkarin.service import (
    ServiceItemsAPIView,
    ServiceProcessDenunciaAPIView,
    ServiceUserDenunciaAPIView,
    ServiceAdminResetPassword,
    DenunciaWizardDataAPIView,
    ConsultaDenunciaAPIView,
    ValidateRutAPIView,              # ⭐ NUEVA API
    AutocompleteUserDataAPIView      # ⭐ NUEVA API
)
from appkarin.service_datatable import (
    DenunciaDataTableAPIView,
    DenunciaDataTableConfigAPIView,
    DenunciaExportAPIView,
    DenunciaDataTableStatsAPIView
)

urlpatterns = [
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
    
    path('api/consulta/denuncia/', 
         csrf_exempt(ConsultaDenunciaAPIView.as_view()), 
         name='consulta_denuncia'),

    path('api/update/admin/password/', 
         csrf_exempt(ServiceAdminResetPassword.as_view()), 
         name='update_password'),


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


    path('api/datatable/denuncias/', 
         csrf_exempt(DenunciaDataTableAPIView.as_view()), 
         name='datatable_denuncias'),
    
    # API de configuración de columnas
    path('api/datatable/denuncias/config/', 
         DenunciaDataTableConfigAPIView.as_view(), 
         name='datatable_config'),
    
    # API de exportación
    path('api/datatable/denuncias/export/', 
         csrf_exempt(DenunciaExportAPIView.as_view()), 
         name='datatable_export'),
    
    # API de estadísticas
    path('api/datatable/denuncias/stats/', 
         DenunciaDataTableStatsAPIView.as_view(), 
         name='datatable_stats'),
    
    # Vista para renderizar el DataTable
    path('admin/denuncias/datatable/', 
         views.renderDataTableDenuncias, 
         name='datatable_view'),
    
    path('denuncias/consulta/', 
         views.renderDataTableDenuncias, 
         name='datatable_view'),


    # =================================================================
    # DJANGO ADMIN
    # =================================================================
    path(settings.ADMIN_URL, admin.site.urls),
]