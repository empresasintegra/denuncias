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
    request.session.flush()
    return response

def renderDataTableDenuncias(request):
    REGEX_DN = re.compile(r'^DN-')
    
    return render(request, 'consultaDenuncia.html')


def renderLoginAdmin(request):

    return render(request, 'login.html')
