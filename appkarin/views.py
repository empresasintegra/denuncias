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

def renderHome(request,empresa):
    print("Empresa solicitada:", empresa)
    _empresa=Empresa.objects.filter(nombre=empresa).first()
    if not _empresa:
        return render(request, 'notfound.html')

    url_logo=f'assets/Logo{empresa}.png'

    if (empresa !='ByF'):
        empresa = re.sub(r'(?<![A-Z\W])(?=[A-Z])', ' ', empresa)
    else:
        empresa = 'B y F'

    context= {
        'url_logo':url_logo,
        'empresa':empresa
    }

    return render(request, 'index.html',context)

def renderItemsDenuncia(request):
    print(request)
    categorias = Categoria.objects.all().prefetch_related('item_set')
    context = {'categorias': categorias}
    
    if request.session.get('empresa_id'):
        return render(request, 'inicioDenuncia.html', context)
    return render(request, 'warning.html', context)

def renderWizzDenuncia(request):
    """Vista única del wizard que carga todos los datos necesarios"""
    if( request.session.get('denuncia_categoria_id')):
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
    else:
        return render(request, 'warning.html')

def renderUserDenuncia(request):


    if(request.session.get('denuncia_categoria_id')):
        if (request.session.get('denuncia_categoria_id')==1):
            return render(request, 'terminoDenunciaLeyKarin.html')
        return render(request, 'terminoDenuncia.html')
    else:
        return render(request, 'warning.html')

def renderCodeDenuncia(request):

    empresa=Empresa.objects.filter(id=request.session.get('empresa_id')).first()

    context = {'code': request.session.get('codigo', ''),'empresa':empresa.nombre}
    response = render(request, 'codeIndex.html', context)
    keys_denuncia = ['item_id', 'wizzard_data', 'codigo','empresa_id']
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
        if codigo:
            # Verificar que el código existe
            if codigo.startswith('DN-'):
                print(f"Código de denuncia recibido: {codigo}")
                # Buscar por código de denuncia directamente
                exists = Denuncia.objects.filter(codigo=codigo).exists()
                if exists:
                    # Guardar el código de denuncia tal cual
                    request.session['codigo_consulta'] = codigo
                    # Redirigir a GET para evitar reenvío de formulario
                    return redirect('consulta_denuncias')
                else:
                    messages.error(request, 'El código de denuncia no existe')
                    # Obtener la empresa de la sesión para redirigir correctamente
                    empresa_id = request.session.get('empresa_id')
                    if empresa_id:
                        empresa = Empresa.objects.filter(id=empresa_id).first()
                        if empresa:
                            return redirect('home', empresa=empresa.nombre)
                    return redirect('hub')
            else:
                # Usuario identificado - código de 5 caracteres
                print(f"Código de usuario recibido: {codigo}")
                exists = Usuario.objects.filter(id=codigo).exists()
                
                if exists:
                    # Guardar en sesión para la consulta
                    request.session['codigo_consulta'] = codigo
                    # Redirigir a GET para evitar reenvío de formulario
                    return redirect('consulta_denuncias')
                else:
                    messages.error(request, 'El código ingresado no existe')
                    # Obtener la empresa de la sesión para redirigir correctamente
                    empresa_id = request.session.get('empresa_id')
                    if empresa_id:
                        empresa = Empresa.objects.filter(id=empresa_id).first()
                        if empresa:
                            return redirect('home', empresa=empresa.nombre)
                    return redirect('hub')
    
    # Para GET, obtener código de URL o sesión
    codigo = request.session.get('codigo_consulta', '')
    
    print(f"Código final enviado al template: {codigo}")
    
    context['codigo'] = codigo
    context['admin_id'] = request.user.id if request.user.is_authenticated else None
    
    # Si es admin, verificar autenticación
    return render(request, 'consultaDenuncia.html', context)

def renderLoginAdmin(request):

    return render(request, 'login.html')


def renderHub(request):

    empresas= Empresa.objects.all()

    nombre_empresas=[]
    url_logos = []
    descripciones=[]
    redirect_urls = []
    
    for empresa in empresas:
        if (empresa.nombre !='ByF'):
             nombre_empresas.append(re.sub(r'(?<![A-Z\W])(?=[A-Z])', ' ', empresa.nombre))
        else:
            nombre_empresas.append('B y F')

        url_logos.append(f'assets/Logo{empresa.nombre}.png')
        redirect_urls.append(f'/{empresa.nombre.lower()}/')  # ← .lower() agregado
        descripciones.append(empresa.descripcion)

    cards_data = zip(nombre_empresas, descripciones, url_logos, redirect_urls)

    context = {
        'cards_data': cards_data
    }

    return render(request, 'hub.html', context)
