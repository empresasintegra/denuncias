from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse
from django.contrib import messages



# Create your views here.
def home(request):
    return render(request, 'index.html')

def itemsDenuncia(request):
    
  
    categorias = Categoria.objects.all().prefetch_related('item_set')
    
    context = {
        'categorias': categorias
    }

    
    return render(request, 'pageItemsDenuncia.html', context)


def getRelacionDenuncia(request):
    
    if request.method == 'POST':
        
        print("denuncia item")

        datos={
            'item': request.POST.get('denuncia_item'),
        }

        if all(datos.values()):
            request.session['datos_denuncia'] = datos
            # REDIRECT: Lleva al usuario a otra página
            return redirect('relacion_empresa')  # URL cambia a 
        else:
            messages.error(request, 'Complete todos los campos')
            # RENDER: Muestra la misma página con error
            return render(request, 'pageItemsDenuncia.html')
    
        # Si no es POST, redirigir al formulario
    return redirect('mostrar_formulario')



def relacionDenuncia(request):
    
    relacionempresa= RelacionEmpresa.objects.all()
    print(relacionempresa[0].rol)


    context = {
        'relacion_empresas': relacionempresa
    }

    
    return render(request, 'pageRelacionDenuncia.html', context)


def descripcionDenuncia(request):
    
    
    return render(request, 'pageItemsDenuncia.html')