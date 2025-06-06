from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import re


# =================================================================
# VISTAS PARA RENDERIZAR TEMPLATES (Sin cambios)
# =================================================================

def renderHome(request):
    return render(request, 'index.html')

def renderItemsDenuncia(request):
    categorias = Categoria.objects.all().prefetch_related('item_set')
    context = {'categorias': categorias}
    return render(request, 'InicioDenuncia.html', context)

def renderWizzDenuncia(request):
    """Vista única del wizard que carga todos los datos necesarios"""
    categorias = Categoria.objects.all().prefetch_related('item_set')
    relacion_empresas = RelacionEmpresa.objects.all()
    tiempos = Tiempo.objects.all()
    wizard_data = request.session.get('wizard_data', {})
    
    context = {
        'categorias': categorias,
        'relacion_empresas': relacion_empresas,
        'tiempos': tiempos,
        'wizard_data': wizard_data,
    }
    return render(request, 'denunciaWizzard.html', context)

def renderUserDenuncia(request):
    return render(request, 'terminoDenuncia.html')

def renderCodeDenuncia(request):
    context = {'code': request.session.get('codigo', '')}
    response = render(request, 'codeIndex.html', context)
    keys_denuncia = ['item_id', 'wizzard_data', 'codigo']
    for key in keys_denuncia:
        if key in request.session:
            del request.session[key]

    return response

def renderConsultaDenuncia(request):
    """
    Renderiza la página de consulta de denuncias
    Detecta el tipo de usuario según el código o sesión
    """
    context = {}
    
    # Verificar si viene un código por POST (desde el index)
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        print(codigo)
        if codigo:
            # Verificar que el código existe
            # Para usuarios anónimos el código es DN-XXXXXXXX pero el ID es solo el DN-XXXXXXXX completo
            if codigo.startswith('DN-'):
                print("estoy en codigo start")
                # Buscar por código de denuncia directamente
                exists = Denuncia.objects.filter(codigo=codigo).exists()
                if exists:
                    # Obtener el ID del usuario de esa denuncia
                    denuncia = Denuncia.objects.filter(codigo=codigo).first()
                    if denuncia:
                        request.session['codigo_consulta'] = codigo = denuncia.usuario.id
            else:
                # Usuario identificado - código de 5 caracteres
                exists = Usuario.objects.filter(id=codigo).exists()
            
                if exists:
                    # Guardar en sesión para la consulta
                    request.session['codigo_consulta'] = codigo
                    # Redirigir a GET para evitar reenvío de formulario
                    return redirect(f'/denuncias/consulta/?codigo={codigo}')
                else:
                    messages.error(request, 'El código ingresado no existe')
                    return redirect('home')
        
    # Para GET, obtener código de URL o sesión
    codigo = request.GET.get('codigo') or request.session.get('codigo_consulta')
    
    if codigo:
        context['codigo'] = codigo
        # Limpiar sesión
        if 'codigo_consulta' in request.session:
            del request.session['codigo_consulta']
    
    # Si es admin, verificar autenticación (esto sería con el sistema de auth real)
    # Por ahora solo pasamos el contexto
    
    return render(request, 'consultaDenuncia.html', context)

def renderLoginAdmin(request):

    return render(request, 'login.html')
