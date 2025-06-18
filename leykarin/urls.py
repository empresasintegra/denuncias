"""
URL configuration for leykarin project - VERSIÓN FINAL CONSOLIDADA
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter
from appkarin import views

# Importar solo los servicios consolidados
from appkarin.service_admin_auth import ServiceAdminDenunciaAuth
from appkarin.service_process_denuncia import ServiceProcessDenuncia
from appkarin.service_consolidated import DenunciaManagementViewSet, DenunciaQueryAPI
from appkarin.service_datatable import SimpleDenunciaDataTableAPIView, ExportDenunciasExcelAPIView
from django.conf import settings
from django.conf.urls.static import static



# Configurar router para ViewSets
router = DefaultRouter()
router.register(r'denuncias', DenunciaManagementViewSet, basename='denuncia-management')

urlpatterns = [
    
    # =================================================================
    # 🔐 AUTENTICACIÓN ADMIN CONSOLIDADA
    # =================================================================
    
    # Rutas de autenticación admin usando un solo servicio
    path('api/admin/auth/<str:action>/', 
         ServiceAdminDenunciaAuth.as_view(), 
         name='admin-auth'),
    
    # Mantener compatibilidad con URLs antiguas
    path('api/admin/login/', 
         ServiceAdminDenunciaAuth.as_view(), 
         {'action': 'login'}, 
         name='admin_login_api'),
    
    path('api/admin/logout/', 
         ServiceAdminDenunciaAuth.as_view(), 
         {'action': 'logout'}, 
         name='admin_logout_api'),
    
    path('api/admin/check-auth/', 
         ServiceAdminDenunciaAuth.as_view(), 
         {'action': 'check'}, 
         name='admin_check_auth_api'),

    # =================================================================
    # 📝 PROCESO DE DENUNCIA CONSOLIDADO
    # =================================================================
    
    # Rutas del proceso de denuncia usando un solo servicio
    path('api/denuncia/initialize',ServiceProcessDenuncia.as_view(),{'step':'initialize'},name='initialize'),
    
    # Mantener compatibilidad con URLs antiguas
    path('api/create/denuncia/items/', 
         ServiceProcessDenuncia.as_view(), 
         {'step': 'items'}, 
         name='process_items'),
    
    path('api/create/denuncia/wizzard/', 
         ServiceProcessDenuncia.as_view(), 
         {'step': 'wizard'}, 
         name='process_denuncia'),
    
    path('api/create/denuncia/user/', 
         ServiceProcessDenuncia.as_view(), 
         {'step': 'user'}, 
         name='process_user'),
    
    path('api/validate/rut/', 
         ServiceProcessDenuncia.as_view(), 
         {'step': 'validate-rut'}, 
         name='validate_rut'),
    
    path('api/autocomplete/user/', 
         ServiceProcessDenuncia.as_view(), 
         {'step': 'autocomplete-user'}, 
         name='autocomplete_user'),
    
    path('api/wizard/data/', 
         ServiceProcessDenuncia.as_view(), 
         {'step': 'wizard-data'}, 
         name='wizard_data'),
    
    path('api/dashboard/denuncia/', 
         ServiceProcessDenuncia.as_view(), 
         {'step': 'consulta'}, 
         name='consulta_denuncia'),

    # =================================================================
    # 🗄️ GESTIÓN DE DENUNCIAS (ViewSet)
    # =================================================================
    
    # ViewSet para gestión de denuncias
    path('api/', include(router.urls)),
    
    # Rutas específicas para mantener compatibilidad
    path('api/denuncia-detalle/<str:codigo>/', 
         DenunciaManagementViewSet.as_view({'get': 'detalle'}), 
         name='denuncia-detalle'),
    
    path('api/denuncia-mensaje/<str:codigo>/', 
         DenunciaManagementViewSet.as_view({'get': 'mensaje'}), 
         name='denuncia-mensaje'),
    
    path('api/denuncia-info/<str:codigo>/', 
         DenunciaManagementViewSet.as_view({'get': 'info'}), 
         name='denuncia-info'),

    path('api/denuncia-envio-mensaje/',
         DenunciaManagementViewSet.as_view({'post':'enviar_mensaje'}), 
         name='denuncia-envio-mensaje'),

    path('api/cambiar-estado-denuncia/', 
         DenunciaManagementViewSet.as_view({'post': 'cambiar_estado'}), 
         name='cambiar-estado'),
    
    path('api/descargar-denuncia/', 
         DenunciaManagementViewSet.as_view({'post': 'descargar'}), 
         name='descargar-denuncia'),

     
    
    # API de consultas complejas
    path('api/denuncias/query/<str:action>/', 
         csrf_exempt(DenunciaQueryAPI.as_view()), 
         name='denuncia-query'),

    # =================================================================
    # 📊 DATATABLES
    # =================================================================
    
    path('api/datatable/denuncias/simple/', 
         csrf_exempt(SimpleDenunciaDataTableAPIView.as_view()), 
         name='datatable_simple'),

     path('api/datatable/denuncias/export/excel/', 
     csrf_exempt(ExportDenunciasExcelAPIView.as_view()), 
     name='datatable_export_excel'),

    # =================================================================
    # 🌐 VISTAS (TEMPLATES)
    # =================================================================
    
    # Páginas principales
    path ('<str:empresa>/',views.renderHome,name='home'),
    path('', views.renderHub, name='hub'),
    path('denuncia/Paso1/', views.renderItemsDenuncia, name='items'),
    path('denuncia/Paso2/', views.renderWizzDenuncia, name='denuncia_wizzard'),
    path('denuncia/Paso3/', views.renderUserDenuncia, name='user_register'),
    path('denuncia/final/', views.renderCodeDenuncia, name='code_view'),
    
    # Admin y consultas
    path('admin/login/', views.renderLoginAdmin, name='login'),
    path('denuncias/consulta/', views.renderConsultaDenuncia, name='consulta_denuncias'),

    # =================================================================
    # 🔧 DJANGO ADMIN
    # =================================================================
    
    path(settings.ADMIN_URL, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)