from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from types import SimpleNamespace
from .models import *






@require_http_methods(["POST"])
def serviceItems(request):

    try:
        if request.POST.get('denuncia_item'):
            request.session['item_id'] = request.POST.get('denuncia_item')
            # REDIRECT: Lleva al usuario a otra página
            return JsonResponse({
                'success': True,
                'message': 'Item procesado correctamente',
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
            'denuncia_descripcion': request.POST.get('descripcion', '').strip(),
            'denuncia_archivos': request.POST.get('archivos')
        }
        
        request.session['wizzard_data'] = data
        print(data)
        # Validar datos
        validation_errors = validate_denuncia_data(data)
        if validation_errors:
            return JsonResponse({
                'success': False,
                'message': validation_errors
            })
        
        else:
            return JsonResponse({
                'success': True,
                'message': 'Wizzard prcesado correctamente',
                'redirect_url': '/denuncia/Paso3/'  # O la URL que corresponda
            })
        
        
        # Crear denuncia
        #denuncia = create_denuncia(data, request)
        
        # Limpiar sesión
        #if 'wizard_data' in request.session:
        #    del request.session['wizard_data']
        
        #return redirect('items')
        
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
            RelacionEmpresa.objects.get(id=data['denuncia_relacion_id'])
        except RelacionEmpresa.DoesNotExist:
            errors.append('Relación con empresa no válida')
    
    # Validar tiempo
    if not data['denuncia_tiempo_id']:
        errors.append('Debe seleccionar hace cuánto tiempo ocurren los hechos')
    else:
        try:
            Tiempo.objects.get(id=data['denuncia_tiempo_id'])
        except Tiempo.DoesNotExist:
            errors.append('Tiempo de denuncia no válido')
    
    # Validar descripción
    if not data['denuncia_descripcion']:
        errors.append('La descripción es obligatoria')
    elif len(data['denuncia_descripcion']) < 50:
        errors.append('La descripción debe tener al menos 50 caracteres')
    
    
    return errors


@require_http_methods(["POST"])
def serviceUserDenuncia(request):

    
    print(request.session)

    try:
            
        item_id=request.session['item_id']
        relacion_id=request.session['wizzard_data']['denuncia_relacion_id']
        tiempo_id=request.session['wizzard_data']['denuncia_tiempo_id']
        descripcion=request.session['wizzard_data']['denuncia_descripcion']
        archivos=request.session['wizzard_data']['denuncia_archivos']

            # 1. Obtener tipo de denuncia del POST
        tipo_denuncia = request.POST.get('tipo_denuncia')
            
            # 2. Crear o buscar usuario según tipo
        if tipo_denuncia == 'anonimo':
                # USUARIOS ANÓNIMOS: Siempre crear nuevo
                usuario = Usuario(anonimo=True)
                usuario.save()  # Se genera ID automáticamente
                
        else:
                # USUARIOS IDENTIFICADOS: Buscar por RUT o crear
            rut_raw = request.POST.get('rut')
                
                # Limpiar RUT para búsqueda consistente
            rut_limpio = re.sub(r'[.-]', '', rut_raw)
            if len(rut_limpio) == 9:
                    rut_formateado = f"{rut_limpio[:2]}.{rut_limpio[2:5]}.{rut_limpio[5:8]}-{rut_limpio[8]}"
            elif len(rut_limpio) == 8:
                    rut_formateado = f"{rut_limpio[:1]}.{rut_limpio[1:4]}.{rut_limpio[4:7]}-{rut_limpio[7]}"
            else:
                    raise ValidationError("Formato de RUT inválido")
                
                # Buscar usuario existente por RUT


            if not Usuario.objects.filter(rut=rut_formateado, anonimo=False).exists():
                # Usuario existe - actualizar datos si es necesario
                usuario = Usuario(
                    anonimo=False,
                    rut=rut_formateado,
                    nombre=request.POST.get('nombre_completo'),
                    apellidos=request.POST.get('apellidos'),
                    correo=request.POST.get('correo_electronico'),
                    celular=request.POST.get('celular')
                )
                usuario.save()
                            
            else :
                usuario=Usuario.objects.get(rut=rut_formateado, anonimo=False)


        print("item?")
        item=Item.objects.get(id=item_id)
        print("esto es item")
        print(item)
        relacion=RelacionEmpresa.objects.get(id=relacion_id)
        tiempo=Tiempo.objects.get(id=tiempo_id)

        denuncia=Denuncia(
            usuario=usuario,
            item=item,
            relacion_empresa=relacion,
            tiempo=tiempo,
            descripcion=descripcion,
        )

        denuncia.save()
            
            
            # 3. Aquí ya tienes el usuario, puedes crear la denuncia directamente
            # O retornar el ID del usuario para el siguiente paso
        print("EL USUARIO HA SIDO GUARDADO")


        return JsonResponse({
                'success': True,
                'user_id': usuario.id,
                'denuncia_id': denuncia.codigo,
                'user_type': 'anonimo' if usuario.anonimo else 'identificado',
                'message': 'Denuncia procesada satisfactoriamente',
                #'redirect_url': reverse('crear_denuncia') 
        })
            
    except ValidationError as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error de validación: {str(e)}'
    })

    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        })