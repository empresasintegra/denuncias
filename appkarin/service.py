from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import *


def serviceItems(request):
    
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
            return redirect('items')
    
        # Si no es POST, redirigir al homr
    return redirect('home')