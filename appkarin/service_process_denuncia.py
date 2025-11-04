# service_process_denuncia.py - Servicio consolidado para todo el proceso de denuncias
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.shortcuts import redirect
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import (
    Categoria, Item, RelacionEmpresa, Tiempo, Usuario, 
    Denuncia, Empresa, Archivo
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
import os
import uuid
import mimetypes
from datetime import datetime
from pathlib import Path


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
    
    # ===== CONFIGURACIÓN DE ARCHIVOS =====
    UPLOAD_FOLDER = 'denuncias/archivos'  # Carpeta dentro de MEDIA_ROOT
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', 
        '.gif', '.xlsx', '.xls', '.txt'
    }
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain'
    }
    
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
        
        print("process")
        empresa_filtrada=Empresa.objects.filter(nombre=empresa).first()

        print("empresa_filtrada")
        print(empresa_filtrada)
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
            print("estoy guardando en session")
            print(item.categoria.id)

            request.session['denuncia_item_id'] = item.id
            request.session['denuncia_item_nombre'] = item.enunciado
            request.session['denuncia_categoria_id']=item.categoria.id
            request.session['denuncia_categoria_nombre'] = item.categoria.nombre
            request.session.modified = True
            request.session.save()
            
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
    
    # ===== PASO 2: WIZARD DE DENUNCIA CON ARCHIVOS =====
    @transaction.atomic
    def _process_wizard(self, request):
        """
        Procesa la información del wizard de denuncia (Paso 2) incluyendo archivos
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
            print("✅ Datos del wizard validados")
            
            # ===== PROCESAR ARCHIVOS (OPCIONAL) =====
            archivos_procesados = []
            archivos_errors = []
            
            # Obtener archivos del request - puede estar vacío
            archivos = request.FILES.getlist('archivos[]')
            print(f"📁 Archivos recibidos: {len(archivos)}")
            
            # ✅ PROCESAR SOLO SI HAY ARCHIVOS
            if archivos and len(archivos) > 0:
                print("📎 Procesando archivos adjuntos...")
                for archivo in archivos:
                    try:
                        # Validar archivo
                        archivo_validado = self._validate_file(archivo)
                        if archivo_validado['valid']:
                            # Guardar archivo físicamente
                            archivo_guardado = self._save_file(archivo)
                            archivos_procesados.append(archivo_guardado)
                            print(f"✅ Archivo guardado: {archivo.name}")
                        else:
                            archivos_errors.append(archivo_validado['error'])
                            print(f"❌ Archivo inválido: {archivo.name} - {archivo_validado['error']}")
                    
                    except Exception as e:
                        error_msg = f"Error al procesar {archivo.name}: {str(e)}"
                        archivos_errors.append(error_msg)
                        print(f"❌ {error_msg}")
                        
                # Si hay errores críticos de archivos Y se intentaron subir archivos, retornar error
                if archivos_errors and not archivos_procesados:
                    return Response({
                        'success': False,
                        'message': 'Errores al procesar archivos',
                        'errors': archivos_errors
                    }, status=400)
            else:
                print("📝 Denuncia sin archivos adjuntos - continuando normalmente")
                # ✅ SIN ARCHIVOS ES VÁLIDO - continuar proceso normal
            
            # Guardar datos en sesión para el siguiente paso
            request.session.update({
                'denuncia_relacion_id': serializer.validated_data['denuncia_relacion'],
                'denuncia_tiempo_id': serializer.validated_data['denuncia_tiempo'],
                'denuncia_descripcion': serializer.validated_data['descripcion'],
                'denuncia_descripcion_relacion': serializer.validated_data.get('descripcion_relacion', '') if serializer.validated_data.get('descripcion_relacion', '') != None else None,
                'archivos_procesados': archivos_procesados  # Guardar info de archivos
            })

            print("✅ Datos guardados en sesión")
            request.session.modified = True
            
            response_data = {
                'success': True,
                'message': 'Información guardada correctamente',
                'redirect_url': '/denuncia/Paso3/'
            }
            
            # ✅ AGREGAR INFORMACIÓN DE ARCHIVOS SOLO SI SE PROCESARON
            if archivos_procesados and len(archivos_procesados) > 0:
                response_data['archivos'] = {
                    'procesados': len(archivos_procesados),
                    'total': len(archivos)
                }
                print(f"📎 Respuesta del wizard incluye info de {len(archivos_procesados)} archivos")
            
            # ✅ INCLUIR WARNINGS DE ARCHIVOS SI LOS HAY (pero no bloquear el proceso)
            if archivos_errors:
                response_data['archivos_warnings'] = archivos_errors
                print(f"⚠️ Warnings de archivos incluidos en respuesta: {len(archivos_errors)}")
            
            return Response(response_data)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=400)
    
    # ===== FUNCIONES DE MANEJO DE ARCHIVOS =====
    
    def _validate_file(self, archivo):
        """
        Valida un archivo subido
        """
        # Validar tamaño
        if archivo.size > self.MAX_FILE_SIZE:
            return {
                'valid': False,
                'error': f'El archivo {archivo.name} excede el tamaño máximo (500MB)'
            }
        
        # Validar extensión
        file_extension = Path(archivo.name).suffix.lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            return {
                'valid': False,
                'error': f'Tipo de archivo no permitido: {file_extension}'
            }
        
        # Validar MIME type (seguridad adicional)
        mime_type, _ = mimetypes.guess_type(archivo.name)
        if mime_type and mime_type not in self.ALLOWED_MIME_TYPES:
            return {
                'valid': False,
                'error': f'Tipo MIME no permitido: {mime_type}'
            }
        
        # Validar que el archivo no esté vacío
        if archivo.size == 0:
            return {
                'valid': False,
                'error': f'El archivo {archivo.name} está vacío'
            }
        
        return {'valid': True}
    
    def _save_file(self, archivo):
        """
        Guarda un archivo en el servidor y retorna la información
        """
        # Generar nombre único para evitar colisiones
        file_extension = Path(archivo.name).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Crear estructura de carpetas por fecha
        fecha_actual = datetime.now()
        folder_path = os.path.join(
            self.UPLOAD_FOLDER,
            str(fecha_actual.year),
            f"{fecha_actual.month:02d}"
        )
        
        # Ruta completa del archivo
        file_path = os.path.join(folder_path, unique_filename)
        
        # Crear directorio si no existe
        full_directory = os.path.join(settings.MEDIA_ROOT, folder_path)
        os.makedirs(full_directory, exist_ok=True)
        
        # Guardar archivo usando Django's file storage
        saved_path = default_storage.save(file_path, ContentFile(archivo.read()))
        
        # Generar URL accesible
        file_url = os.path.join(settings.MEDIA_URL, saved_path)
        
        return {
            'original_name': archivo.name,
            'saved_name': unique_filename,
            'path': saved_path,
            'url': file_url,
            'size': archivo.size,
            'mime_type': archivo.content_type
        }
    
    def _create_archivo_records(self, denuncia, archivos_info):
        """
        Crea registros en la base de datos para los archivos.
        ✅ Maneja correctamente listas vacías (retorna lista vacía)
        """
        archivos_creados = []
        
        # ✅ SI NO HAY ARCHIVOS, RETORNAR LISTA VACÍA (no es error)
        if not archivos_info or len(archivos_info) == 0:
            print("📝 No hay archivos para registrar en base de datos")
            return archivos_creados
        
        for archivo_info in archivos_info:
            try:
                archivo_record = Archivo.objects.create(
                    denuncia=denuncia,
                    url=archivo_info['url'],
                    nombre=archivo_info['original_name'],
                    descripción=f"Archivo adjunto: {archivo_info['original_name']}",
                    Peso=archivo_info['size']
                )
                archivos_creados.append(archivo_record)
                print(f"✅ Registro de archivo creado: {archivo_record.nombre}")
                
            except Exception as e:
                print(f"❌ Error al crear registro para {archivo_info['original_name']}: {str(e)}")
                # Opcional: eliminar archivo físico si no se pudo crear el registro
                try:
                    default_storage.delete(archivo_info['path'])
                    print(f"🗑️ Archivo físico eliminado: {archivo_info['path']}")
                except Exception as delete_error:
                    print(f"⚠️ No se pudo eliminar archivo huérfano: {delete_error}")
        
        return archivos_creados
    
    # ===== PASO 3: REGISTRO DE USUARIO Y CREACIÓN DE DENUNCIA =====
    @transaction.atomic
    def _process_user(self, request):
        """
        Procesa el registro de usuario y crea la denuncia (Paso 3)
        """
        # Verificar datos previos en sesión
        required_session_keys = [
            'denuncia_item_id', 'denuncia_relacion_id', 
            'denuncia_categoria_id','denuncia_categoria_nombre',
            'denuncia_tiempo_id', 'denuncia_descripcion'
        ]

        print(required_session_keys)
        print("?")
        
        missing_keys = [key for key in required_session_keys if not request.session.get(key)]
        print(missing_keys)
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
                descripcion_relacion=request.session.get('denuncia_descripcion_relacion', '') if request.session['denuncia_descripcion_relacion'] else ''
            )
            
            # ===== PROCESAR ARCHIVOS SI EXISTEN =====
            archivos_procesados = request.session.get('archivos_procesados', [])
            archivos_creados = []
            
            if archivos_procesados and len(archivos_procesados) > 0:
                print(f"📁 Creando registros para {len(archivos_procesados)} archivos")
                archivos_creados = self._create_archivo_records(denuncia, archivos_procesados)
                print(f"✅ {len(archivos_creados)} archivos registrados en base de datos")
            else:
                print("📝 Denuncia creada sin archivos adjuntos")
            
            # Limpiar sesión (incluyendo archivos si los había)
            for key in required_session_keys + ['archivos_procesados']:
                request.session.pop(key, None)
            
            # Guardar código para mostrar en página final
            request.session['codigo'] = denuncia.codigo if usuario.anonimo else usuario.id
            request.session['denuncia_created'] = True  # Flag adicional
            request.session.modified = True  # ✅ CRÍTICO: Forzar guardado
            request.session.save()  # ✅ CRÍTICO: Guardar inmediatamente
            
            
            response_data = {
                'success': True,
                'message': 'Denuncia creada exitosamente',
                'data': {
                    'codigo': request.session['codigo'],
                    'es_anonima': usuario.anonimo,
                    'denuncia_id': denuncia.codigo
                },
            }
            
            # ✅ AGREGAR INFORMACIÓN DE ARCHIVOS SOLO SI EXISTEN
            if archivos_creados and len(archivos_creados) > 0:
                response_data['data']['archivos'] = {
                    'total': len(archivos_creados),
                    'nombres': [archivo.nombre for archivo in archivos_creados]
                }
                print(f"📎 Respuesta incluye info de {len(archivos_creados)} archivos")
            else:
                print("📝 Respuesta sin información de archivos (no se adjuntaron)")
            
            return Response(response_data)
        
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