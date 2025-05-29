from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import *


def serviceItems(request):
    
    if request.method == 'POST':
        
        print("denuncia item")

        datos={
            'item': request.POST.get('denuncia_item'),
        }

        if all(datos.values()):
            request.session['item'] = datos
            # REDIRECT: Lleva al usuario a otra página
            return redirect('denuncia_wizzard')  # URL cambia a 
        else:
            messages.error(request, 'Complete todos los campos')
            # RENDER: Muestra la misma página con error
            return redirect('items')
    
        # Si no es POST, redirigir al home
    return redirect('home')


@require_http_methods(["POST"])
def serviceProcessDenuncia(request):
    """
    Procesa la denuncia completa del wizard
    Reemplaza: getRelacionDenuncia, process_descripcion, process_tiempo
    """
    try:
        # Extraer datos del formulario
        data = {
            'denuncia_item': request.POST.get('denuncia_item'),
            'denuncia_relacion': request.POST.get('denuncia_relacion'),
            'denuncia_tiempo': request.POST.get('denuncia_tiempo'),
            'descripcion': request.POST.get('descripcion', '').strip(),
            'acepta_terminos': request.POST.get('acepta_terminos') == 'true',
        }
        
        print("Datos recibidos:", data)  # Para debug
        
        # Validar datos
        validation_errors = validate_denuncia_data(data)
        if validation_errors:
            return JsonResponse({
                'success': False,
                'message': validation_errors[0]
            })
        
        # Crear denuncia
        #denuncia = create_denuncia(data, request)
        
        # Limpiar sesión
        if 'wizard_data' in request.session:
            del request.session['wizard_data']
        
        return redirect('items')
        
    except Exception as e:
        print(f"Error al procesar denuncia: {str(e)}")  # Para debug
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor. Por favor intente nuevamente.'
        })

def validate_denuncia_data(data):
    """Validar todos los datos del wizard"""
    errors = []
    
    # Validar tipo de denuncia
    if not data['denuncia_item']:
        errors.append('Debe seleccionar un tipo de denuncia')
    else:
        try:
            Item.objects.get(id=data['denuncia_item'])
        except Item.DoesNotExist:
            errors.append('Tipo de denuncia no válido')
    
    # Validar relación empresa
    if not data['denuncia_relacion']:
        errors.append('Debe seleccionar su relación con la empresa')
    else:
        try:
            RelacionEmpresa.objects.get(id=data['denuncia_relacion'])
        except RelacionEmpresa.DoesNotExist:
            errors.append('Relación con empresa no válida')
    
    # Validar tiempo
    if not data['denuncia_tiempo']:
        errors.append('Debe seleccionar hace cuánto tiempo ocurren los hechos')
    else:
        try:
            Tiempo.objects.get(id=data['denuncia_tiempo'])
        except Tiempo.DoesNotExist:
            errors.append('Tiempo de denuncia no válido')
    
    # Validar descripción
    if not data['descripcion']:
        errors.append('La descripción es obligatoria')
    elif len(data['descripcion']) < 20:
        errors.append('La descripción debe tener al menos 20 caracteres')
    
    # Validar términos
    if not data['acepta_terminos']:
        errors.append('Debe aceptar los términos y condiciones')
    
    return errors