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
from appkarin import views, service


urlpatterns = [


    #RENDER VIEWS
    path('',views.home,name='home'),
    path('denuncia/Paso1/',views.itemsDenuncia,name='items'),
    path('denuncia/Paso2/',views.relacionDenuncia,name='relacion_empresa'),
    path('denuncia/Paso3/',views.descripcionDenuncia,name='descripcion'),




    #APIS
    path('api/denuncia/items/', service.serviceItems, name='process_items'),


    path(settings.ADMIN_URL, admin.site.urls),
]
