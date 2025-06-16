# service_process_denuncia.py - Servicio consolidado para todo el proceso de denuncias
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.shortcuts import redirect
from .models import (
    Categoria, Item, RelacionEmpresa, Tiempo, Usuario, 
    Denuncia, Empresa
)
from .serializers import (
    ItemSelectionSerializer, DenunciaCreateSerializer, 
    UsuarioCreateSerializer,
    CategoriaWithItemsSerializer, RelacionEmpresaSerializer, 
    TiempoSerializer,EmpresaSerializer
)
from .utils import (
    validate_rut
)

import time
import secrets
import string
from datetime import datetime


@method_decorator(csrf_exempt, name='dispatch')
class ServiceProcessDenuncia(APIView):
    """
    Servicio consolidado para todo el flujo de creación y consulta de denuncias.
    
    Reemplaza:
    - ServiceItemsAPIView
    - ServiceProcessDenunciaAPIView
    - ServiceUserDenunciaAPIView
    - DenunciaWizardDataAPIView
    - ConsultaDenunciaAPIView
    - ValidateRutAPIView
    - AutocompleteUserDataAPIView
    """
    
    def post(self, request, step=None):
        """
        POST /api/denuncia/process/{step}/
        
        Steps disponibles:
        - items: Seleccionar tipo de denuncia (Paso 1)
        - wizard: Completar información de denuncia (Paso 2)
        - user: Registrar usuario (Paso 3)
        - validate-rut: Validar RUT chileno
        - autocomplete-user: Autocompletar datos de usuario por RUT
        - consulta: Consultar estado de denuncia
        """

        print("hola?")
        try:
            print("estoy en try")

            if step == 'initialize':
                print("estoy en initilize")
                return self._process_initialize(request)
            elif step == 'items':
                return self._process_items(request)
            elif step == 'wizard':
                return self._process_wizard(request)
            elif step == 'user':
                return self._process_user(request)
            elif step == 'validate-rut':
                return self._validate_rut(request)
            elif step == 'autocomplete-user':
                return self._autocomplete_user(request)
            elif step == 'consulta':
                return self._consulta_denuncia(request)
            else:
                return Response({
                    'success': False,
                    'message': f'Paso no válido: {step}'
                }, status=400)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error en proceso: {str(e)}'
            }, status=500)
    
    def get(self, request, step=None):
        """
        GET /api/denuncia/process/{step}/
        
        Para obtener datos necesarios para el wizard
        """
        if step == 'wizard-data':
            return self._get_wizard_data(request)
        elif step == 'categories':
            return self._get_categories_items(request)
        
        return Response({
            'success': False,
            'message': 'Método no permitido'
        }, status=405)
    # ===== PASO 1: INICIACIÓN DE LA DENUNCIA =====
    def _process_initialize(self,request):
       
        empresa=request.data['empresa']
        empresa="".join(empresa.split())

        empresa_filtrada=Empresa.objects.filter(nombre=empresa).first()
        request.session['empresa_id']=empresa_filtrada.id
        print(empresa_filtrada.id)

        return Response({
                'success': True,
                'message': 'Item seleccionado correctamente',
                'redirect_url': '/denuncia/Paso1/',
            })



    # ===== PASO 2: SELECCIÓN DE ITEMS =====
    def _process_items(self, request):
        """
        Procesa la selección del tipo de denuncia (Paso 1)
        """
        serializer = ItemSelectionSerializer(data=request.data)
        
        if serializer.is_valid():
            item = serializer.get_validated_item()
            
            # Guardar en sesión
            request.session['denuncia_item_id'] = item.id
            request.session['denuncia_item_nombre'] = item.enunciado
            request.session['denuncia_categoria_id']=item.categoria.id
            request.session['denuncia_categoria_nombre'] = item.categoria.nombre
            request.session.modified = True
            
            return Response({
                'success': True,
                'message': 'Item seleccionado correctamente',
                'data': {
                    'item_id': item.id,
                    'item_nombre': item.enunciado,
                    'categoria': item.categoria.nombre
                },
                'redirect_url': '/denuncia/Paso2/'
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=400)
    
    # ===== PASO 2: WIZARD DE DENUNCIA =====
    def _process_wizard(self, request):
        """
        Procesa la información del wizard de denuncia (Paso 2)
        """
        # Verificar que haya item seleccionado
        item_id = request.session.get('denuncia_item_id')
        if not item_id:
            return Response({
                'success': False,
                'message': 'Debe seleccionar un tipo de denuncia primero',
                'redirect': '/denuncia/Paso1/'
            }, status=400)
        
        # Agregar item_id a los datos
        data = request.data.copy()
        data['item_id'] = item_id
        
        serializer = DenunciaCreateSerializer(data=data)
        
        if serializer.is_valid():
            # Guardar datos en sesión para el siguiente paso
            print("validate")
            request.session.update({
                'denuncia_relacion_id': serializer.validated_data['denuncia_relacion'],
                'denuncia_tiempo_id': serializer.validated_data['denuncia_tiempo'],
                'denuncia_descripcion': serializer.validated_data['descripcion'],
                'denuncia_descripcion_relacion': serializer.validated_data.get('descripcion_relacion', '') if serializer.validated_data.get('descripcion_relacion', '') !=None else None
            })

            print("validated?")
            request.session.modified = True
            
            return Response({
                'success': True,
                'message': 'Información guardada correctamente',
                'redirect_url': '/denuncia/Paso3/'
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=400)
    
    # ===== PASO 3: REGISTRO DE USUARIO Y CREACIÓN DE DENUNCIA =====
    @transaction.atomic
    def _process_user(self, request):
        """
        Procesa el registro de usuario y crea la denuncia (Paso 3)
        """
        # Verificar datos previos en sesión
        required_session_keys = [
            'denuncia_item_id', 'denuncia_relacion_id', 
            'denuncia_categoria_id','denuncia_categoria_nombre'
            'denuncia_tiempo_id', 'denuncia_descripcion','denuncia_descripcion_relacion'
        ]
        
        missing_keys = [key for key in required_session_keys if not request.session.get(key)]
        if missing_keys:
            return Response({
                'success': False,
                'message': 'Datos incompletos. Debe completar los pasos anteriores.',
                'missing': missing_keys,
                'redirect': '/denuncia/Paso1/'
            }, status=400)

        print(request.data)        
        tipo_denuncia = request.data.get('tipo_denuncia')

        usuario_data = {
                'anonimo': tipo_denuncia == 'anonimo',
                'rut': request.data.get('rut', ''),
                'nombre': request.data.get('nombre_completo', ''),
                'apellidos': request.data.get('apellidos', ''),
                'correo': request.data.get('correo_electronico', ''),
                'celular': request.data.get('celular', '')
        }

        # Procesar datos de usuario
        user_serializer = UsuarioCreateSerializer(data=usuario_data)
        print("user?")  
        if user_serializer.is_valid():
            # Crear o actualizar usuario
            usuario = user_serializer.update_or_create()
            print("id usuario ")
            # Generar código único
            # Crear denuncia
            print("create?")
            print (request.session['empresa_id'])
            denuncia = Denuncia.objects.create(
                usuario=usuario,
                item_id=request.session['denuncia_item_id'],
                tipo_empresa_id=request.session['empresa_id'],
                relacion_empresa_id=request.session['denuncia_relacion_id'],
                tiempo_id=request.session['denuncia_tiempo_id'],
                descripcion=request.session['denuncia_descripcion'],
                descripcion_relacion=request.session.get('denuncia_descripcion_relacion', ''),
            )
            
            # Limpiar sesión
            for key in required_session_keys:
                request.session.pop(key, None)
            
            # Guardar código para mostrar en página final
            request.session['codigo'] = denuncia.codigo if usuario.anonimo else usuario.id

            print(request.session['codigo'])
            
            return Response({
                'success': True,
                'message': 'Denuncia creada exitosamente',
                'data': {
                    'codigo': request.session['codigo'],
                    'es_anonima': usuario.anonimo
                },
                'redirect_url': '/denuncia/final/'
            })
        
        return Response({
            'success': False,
            'errors': user_serializer.errors
        }, status=400)
    
    # ===== VALIDACIÓN DE RUT =====
    def _validate_rut(self, request):
        """
        Valida un RUT chileno en tiempo real
        """
        try:
            # ✅ SIMULAR DELAY DEL SERVIDOR (2 segundos máximo)
            time.sleep(0.5)  # Simular tiempo de respuesta del servidor
            
            # ✅ OBTENER Y LIMPIAR RUT
            rut_input = request.data.get('rut', '').strip()
            
            if not rut_input:
                return Response({
                    'success': False,
                    'valid': False,
                    'exists': False,
                    'message': 'RUT requerido'
                }, status=400, json_dumps_params={'ensure_ascii': False})
            
            print(f"🔍 Validando RUT: {rut_input}")
            
            # ✅ VALIDAR FORMATO DE RUT
            try:
                validate_rut(rut_input)
                print("✅ RUT con formato válido")
            except Exception as e:
                print(f"❌ RUT con formato inválido: {str(e)}")
                return Response({
                    'success': True,  # Success porque la operación se completó
                    'valid': False,
                    'exists': False,
                    'message': f'RUT inválido: {str(e)}',
                    'error_type': 'format_error'
                }, status=200)
            
            # ✅ BUSCAR RUT EN BASE DE DATOS
            try:
                # Limpiar RUT para búsqueda (remover puntos y guión)
                
                # Buscar usuario con este RUT
                usuario_existente = Usuario.objects.filter(
                    rut__iexact=rut_input
                ).first()
                
                if usuario_existente:
                    print(f"⚠️ RUT ya existe - Usuario ID: {usuario_existente.id}")
                    
                    # ✅ RUT EXISTE - Preparar información del usuario
                    user_info = {
                        'id': usuario_existente.id,
                        'nombre_completo': usuario_existente.nombre_completo,
                        'correo': usuario_existente.correo if not usuario_existente.anonimo else None,
                        'celular': usuario_existente.celular if not usuario_existente.anonimo else None,
                        'es_anonimo': usuario_existente.anonimo,
                        'fecha_registro': usuario_existente.fecha_creacion.strftime('%d/%m/%Y'),
                        'total_denuncias': usuario_existente.denuncia_set.count()
                    }
                    
                    return Response({
                        'success': True,
                        'valid': True,
                        'exists': True,
                        'message': 'Este RUT ya está registrado en nuestro sistema',
                        'user_info': user_info,
                        'suggestion': 'Sus datos pueden ser autocompletados'
                    }, status=200)
                    
                else:
                    print("✅ RUT válido y disponible")
                    
                    # ✅ RUT VÁLIDO Y NO EXISTE
                    return Response({
                        'success': True,
                        'valid': True,
                        'exists': False,
                        'message': 'RUT válido y disponible',
                        'suggestion': 'Puede continuar con el registro'
                    }, status=200)
                    
            except Exception as e:
                print(f"❌ Error al buscar en base de datos: {str(e)}")
                return Response({
                    'success': False,
                    'valid': True,  # Formato OK, pero error en DB
                    'exists': False,
                    'message': 'Error al verificar RUT en la base de datos',
                    'error_type': 'database_error'
                }, status=500)
                
        except Exception as e:
            print(f"❌ Error general en validación de RUT: {str(e)}")
            return Response({
                'success': False,
                'valid': False,
                'exists': False,
                'message': 'Error interno del servidor',
                'error_type': 'server_error'
            }, status=500)
    
    # ===== AUTOCOMPLETAR USUARIO =====
    def _autocomplete_user(self, request):
        """
        Autocompletar datos de usuario basado en RUT
        """
        rut = request.data.get('rut', '').strip()
        
        if not rut:
            return Response({
                'success': False,
                'message': 'RUT requerido'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(rut=rut, anonimo=False)
            
            usuario = Usuario.objects.filter(rut__iexact=rut).first()
            
            if usuario and not usuario.anonimo:
                # Solo autocompletar si no es anónimo
                return Response({
                    'success': True,
                    'autocomplete_data': {
                        'nombre_completo': usuario.nombre,
                        'apellidos': usuario.apellidos,
                        'correo_electronico': usuario.correo,
                        'celular': usuario.celular.replace('+569', '') if usuario.celular else ''
                    },
                    'message': 'Datos encontrados y autocompletados'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'No se encontraron datos para autocompletar'
                }, status=404)
        except Usuario.DoesNotExist:
            return Response({
                'success': True,
                'found': False,
                'message': 'Usuario no encontrado'
            })
    
    # ===== CONSULTA DE DENUNCIA =====
    def _consulta_denuncia(self, request):
        """
        Consultar estado de denuncia por código
        """
        codigo = request.data.get('codigo', '').strip().upper()
        
        if not codigo:
            return Response({
                'success': False,
                'message': 'Código requerido'
            }, status=400)
        
        # Determinar tipo de consulta
        if codigo.startswith('DN-'):
            # Denuncia anónima
            denuncias = Denuncia.objects.filter(codigo=codigo)
            tipo_consulta = 'anonima'
        else:
            # Usuario identificado - buscar por ID
            try:
                # Intentar convertir a número (ID de usuario)
                user_id = int(codigo)
                denuncias = Denuncia.objects.filter(usuario__id=user_id)
                tipo_consulta = 'identificada'
            except ValueError:
                return Response({
                    'success': False,
                    'message': 'Formato de código inválido'
                }, status=400)
        
        if denuncias.exists():
            # Preparar datos para la sesión
            if tipo_consulta == 'anonima':
                request.session['codigo_consulta'] = codigo
                request.session['tipo_consulta'] = 'anonima'
            else:
                usuario = denuncias.first().usuario
                request.session['codigo_consulta'] = str(usuario.id).zfill(5)
                request.session['tipo_consulta'] = 'identificada'
                request.session['user_name'] = usuario.nombre_completo
            
            return Response({
                'success': True,
                'found': True,
                'count': denuncias.count(),
                'tipo': tipo_consulta,
                'redirect_url': '/denuncias/consulta/'
            })
        
        return Response({
            'success': False,
            'found': False,
            'message': 'No se encontraron denuncias con ese código'
        }, status=404)
    
    # ===== OBTENER DATOS PARA WIZARD =====
    def _get_wizard_data(self, request):
        """
        Obtiene todos los datos necesarios para el wizard
        """
        # Verificar que haya item seleccionado
        item_id = request.session.get('denuncia_item_id')
        if not item_id:
            return Response({
                'success': False,
                'message': 'Debe seleccionar un tipo de denuncia primero'
            }, status=400)
        
        # Obtener datos
        relaciones = RelacionEmpresa.objects.all()
        tiempos = Tiempo.objects.all()
        
        # Obtener item seleccionado
        try:
            item = Item.objects.select_related('categoria').get(id=item_id)
            item_data = {
                'id': item.id,
                'enunciado': item.enunciado,
                'categoria': item.categoria.nombre
            }
        except Item.DoesNotExist:
            item_data = None
        
        return Response({
            'success': True,
            'data': {
                'item_seleccionado': item_data,
                'relacion_empresas': RelacionEmpresaSerializer(relaciones, many=True).data,
                'tiempos': TiempoSerializer(tiempos, many=True).data
            }
        })
    
    # ===== OBTENER CATEGORÍAS E ITEMS =====
    def _get_categories_items(self, request):
        """
        Obtiene todas las categorías con sus items
        """
        categorias = Categoria.objects.prefetch_related('item_set').all()
        serializer = CategoriaWithItemsSerializer(categorias, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    # ===== HELPERS =====
    def _generar_codigo_anonimo(self):
        """
        Genera un código único para denuncias anónimas
        Formato: DN-XXXXXXXX (8 caracteres aleatorios)
        """
        while True:
            # Generar código aleatorio
            random_part = ''.join(
                secrets.choice(string.ascii_uppercase + string.digits) 
                for _ in range(8)
            )
            codigo = f'DN-{random_part}'
            
            # Verificar que no exista
            if not Denuncia.objects.filter(codigo=codigo).exists():
                return codigo