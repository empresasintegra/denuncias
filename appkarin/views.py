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

    REGEX_DN = re.compile(r'^DN-')
    denuncias_data=[]


    if not request.session.get('admin'):
        if request.method == 'POST':
            codigo=request.POST.get('codigo')

            if bool(REGEX_DN.match(codigo)):
                denuncia = Denuncia.objects.select_related(
                    'usuario',
                    'item',
                    'item__categoria',
                    'relacion_empresa',
                    'tiempo'
                ).filter(codigo=codigo).first()
                denuncias_data.append(denuncia)
            else:
                denuncias = Denuncia.objects.select_related(
                    'usuario',
                    'item',
                    'item__categoria',
                    'relacion_empresa',
                    'tiempo'
                ).filter(usuario_id=codigo).first()

                for denuncia in denuncias:
                    denuncias_data.append(denuncia)

    else:
        denuncias = Denuncia.objects.select_related(
                'usuario',
                'item',
                'item__categoria',
                'relacion_empresa',
                'tiempo'
        ).all()

        for denuncia in denuncias:
            denuncias_data.append(denuncia)


    context = {
        'denuncias_data': denuncias_data,
        'total_denuncias': len(denuncias_data),
        'admin': False,
    }
    
    
    return render(request, 'consultaDenuncia.html',context)