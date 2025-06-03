from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse
from django.contrib import messages



# Create your views here.
def renderHome(request):
    return render(request, 'index.html')

def renderItemsDenuncia(request):
    
  
    categorias = Categoria.objects.all().prefetch_related('item_set')
    
    context = {
        'categorias': categorias
    }

    
    return render(request, 'InicioDenuncia.html', context)


def renderWizzDenuncia(request):
    """
    Vista única del wizard que carga todos los datos necesarios
    Reemplaza tus vistas: itemsDenuncia, relacionDenuncia, descripcionDenuncia
    """
    # Cargar todos los datos para todos los pasos
    categorias = Categoria.objects.all().prefetch_related('item_set')
    relacion_empresas = RelacionEmpresa.objects.all()
    tiempos = Tiempo.objects.all()  # Necesitas crear este modelo si no existe
    
    # Datos de sesión para repoblar formulario si existe
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


    context = {
        'code': request.session['codigo'],
    }
    
    response = render(request, 'codeIndex.html', context)
    request.session.flush()  # Elimina TODO y regenera session key
    
    return response



def renderConsultaDenuncia(request):


    context = {
        'code': request.session['codigo'],
    }
    
    response = render(request, 'codeIndex.html', context)
    request.session.flush()  # Elimina TODO y regenera session key
    
    return response