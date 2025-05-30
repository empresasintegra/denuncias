from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import *






@require_http_methods(["POST"])
def serviceItems(request):
    

    datos={
        'item': request.POST.get('denuncia_item'),
    }

    try:
        if all(datos.values()):
            print("estamos en datos values")
            request.session['item_id'] = datos
            print("datos",datos)
            # REDIRECT: Lleva al usuario a otra página
            return JsonResponse({
                'success': True,
                'message': 'Denuncia procesada correctamente',
                'redirect_url': '/denuncia/Paso2/'  # O la URL que corresponda
            })
        else:
            # RENDER: Muestra la misma página con error
            return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar el tipo de denuncia'
                })
        
    except Exception as e:
        print(f"Error al procesar denuncia: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor. Por favor intente nuevamente.'
        })



        
        
    


@require_http_methods(["POST"])
def serviceProcessDenuncia(request):
    """
    Procesa la denuncia completa del wizard
    Reemplaza: getRelacionDenuncia, process_descripcion, process_tiempo
    """
    try:
        # Extraer datos del formulario
        data = {
            'denuncia_relacion_id': int(request.POST.get('denuncia_relacion')),
            'denuncia_tiempo_id': int(request.POST.get('denuncia_tiempo')),
            'descripcion': request.POST.get('descripcion', '').strip(),

        }
        
        print("Datos recibidos:", data)  # Para debug
        request.session['wizzard_data'] = data
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
    
    # Validar relación empresa
    if not data['denuncia_relacion_id']:
        errors.append('Debe seleccionar su relación con la empresa')
    else:
        try:
            RelacionEmpresa.objects.get(id=data['denuncia_relacion'])
        except RelacionEmpresa.DoesNotExist:
            errors.append('Relación con empresa no válida')
    
    # Validar tiempo
    if not data['denuncia_tiempo_id']:
        errors.append('Debe seleccionar hace cuánto tiempo ocurren los hechos')
    else:
        try:
            Tiempo.objects.get(id=data['denuncia_tiempo'])
        except Tiempo.DoesNotExist:
            errors.append('Tiempo de denuncia no válido')
    
    # Validar descripción
    if not data['descripcion']:
        errors.append('La descripción es obligatoria')
    elif len(data['descripcion']) < 50:
        errors.append('La descripción debe tener al menos 50 caracteres')
    
    
    return errors