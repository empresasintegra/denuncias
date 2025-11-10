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
    TiempoSerializer, EmpresaSerializer
)

import time
import secrets
import string
import os
import uuid
import mimetypes
from datetime import datetime
from pathlib import Path


def validate_rut(rut):
    """
    Valida un RUT chileno y retorna (es_valido, rut_formateado)
    
    Args:
        rut (str): RUT en cualquier formato (con o sin puntos y guión)
    
    Returns:
        tuple: (bool, str) - (es_válido, rut_formateado) o (False, None) si es inválido
    """
    if not rut or not isinstance(rut, str):
        return (False, None)
    
    try:
        # Limpiar el RUT: remover puntos, guiones y espacios
        rut_limpio = rut.replace('.', '').replace('-', '').replace(' ', '').upper()
        
        # Verificar que tenga al menos 2 caracteres (número + dígito verificador)
        if len(rut_limpio) < 2:
            return (False, None)
        
        # Separar cuerpo y dígito verificador
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        
        # Verificar que el cuerpo sea numérico
        if not cuerpo.isdigit():
            return (False, None)
        
        # Verificar que el dígito verificador sea válido (0-9 o K)
        if dv not in '0123456789K':
            return (False, None)
        
        # Calcular dígito verificador esperado
        suma = 0
        multiplo = 2
        
        for digito in reversed(cuerpo):
            suma += int(digito) * multiplo
            multiplo += 1
            if multiplo == 8:
                multiplo = 2
        
        resto = suma % 11
        dv_esperado = 11 - resto
        
        # Convertir dígito verificador esperado
        if dv_esperado == 11:
            dv_esperado = '0'
        elif dv_esperado == 10:
            dv_esperado = 'K'
        else:
            dv_esperado = str(dv_esperado)
        
        # Validar
        es_valido = (dv == dv_esperado)
        
        if es_valido:
            # Formatear RUT: XX.XXX.XXX-X
            cuerpo_formateado = f"{int(cuerpo):,}".replace(',', '.')
            rut_formateado = f"{cuerpo_formateado}-{dv}"
            return (True, rut_formateado)
        else:
            return (False, None)
            
    except Exception as e:
        print(f"Error en validación de RUT: {str(e)}")
        return (False, None)


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
    UPLOAD_FOLDER = 'denuncias/archivos'  # Carpeta dentro de S3
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

        try:

            if step == 'initialize':
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


    def _process_initialize(self, request):
        """
        Inicializa el proceso de denuncia seleccionando la empresa
        """
        empresa = request.data.get('empresa', '')
        empresa = "".join(empresa.split())
    
        empresa_filtrada = Empresa.objects.filter(nombre=empresa).first()

        if not empresa_filtrada:
            return Response({
                'success': False,
                'message': 'Empresa no encontrada'
            }, status=404)

        request.session['empresa_id'] = empresa_filtrada.id
        
        return Response({
            'success': True,
            'message': 'Empresa seleccionada correctamente',
            'redirect_url': '/denuncia/Paso1/',
        })

    # ===== PASO 1: SELECCIÓN DE ITEMS =====
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
            request.session['denuncia_categoria_id'] = item.categoria.id
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
        Guarda archivos temporalmente para procesarlos en el siguiente paso
        """
        
        archivos_temp_paths = []  
        
        try:
            # Verificar que haya item seleccionado
            item_id = request.session.get('denuncia_item_id')
            if not item_id:
                return Response({
                    'success': False,
                    'message': 'Debe seleccionar un tipo de denuncia primero',
                    'redirect': '/denuncia/Paso1/'
                }, status=400)
            
            # MAPEAR los nombres de campos del frontend a los esperados por el serializer
            data = {
                'item_id': item_id,
                'relacion_empresa_id': request.data.get('denuncia_relacion'),
                'tiempo_id': request.data.get('denuncia_tiempo'),
                'descripcion': request.data.get('descripcion'),
                'descripcion_relacion': request.data.get('descripcion_relacion', '')
            }
            
            
            serializer = DenunciaCreateSerializer(data=data)
            
            if serializer.is_valid():
                
                # ===== PROCESAR ARCHIVOS (OPCIONAL) =====
                archivos_procesados = []
                archivos_errors = []
                
                # Obtener archivos del request
                archivos = request.FILES.getlist('archivos[]')
                
                # PROCESAR SOLO SI HAY ARCHIVOS
                if archivos and len(archivos) > 0:
                    for archivo in archivos:
                        try:
                            # Validar archivo
                            archivo_validado = self._validate_file(archivo)
                            if archivo_validado['success']:
                                archivos_procesados.append({
                                    'file': archivo,
                                    'nombre': archivo.name,
                                    'size': archivo.size,
                                    'type': archivo.content_type
                                })
                            else:
                                archivos_errors.append(archivo_validado['message'])
                                print(f"❌ Archivo inválido: {archivo_validado['message']}")
                                
                        except Exception as e:
                            error_msg = f"Error procesando {archivo.name}: {str(e)}"
                            archivos_errors.append(error_msg)
                            print(f"❌ {error_msg}")
                    
                    # Si hay errores en archivos, retornar sin crear la denuncia
                    if archivos_errors:
                        return Response({
                            'success': False,
                            'message': 'Error en archivos adjuntos',
                            'errors': archivos_errors
                        }, status=400)
                
                if archivos_procesados:
                    # Guardar archivos temporalmente DIRECTAMENTE en MEDIA_ROOT (sin carpeta)
                    # Usamos prefijo "temp_" para identificarlos y eliminarlos después
                    
                    # Guardar archivos temporalmente
                    for archivo_info in archivos_procesados:
                        archivo = archivo_info['file']
                        # Generar nombre único con prefijo temporal
                        temp_filename = f"temp_{uuid.uuid4()}_{archivo.name}"
                        temp_path = os.path.join(settings.MEDIA_ROOT, temp_filename)
                        
                        try:
                            # Guardar archivo temporalmente
                            with open(temp_path, 'wb+') as destination:
                                for chunk in archivo.chunks():
                                    destination.write(chunk)
                            
                            archivos_temp_paths.append({
                                'temp_path': temp_path,
                                'original_name': archivo.name,
                                'size': archivo.size,
                                'type': archivo.content_type
                            })
                            print(f"✅ Archivo guardado temporalmente: {temp_filename}")
                        except Exception as e:
                            print(f"❌ Error guardando archivo temporalmente: {str(e)}")
                            # Limpiar archivos ya guardados antes de retornar error
                            self._cleanup_temp_files([a['temp_path'] for a in archivos_temp_paths])
                            raise
                    
                    # Guardar rutas en sesión
                    request.session['archivos_temp_paths'] = archivos_temp_paths
                    print(f"✅ {len(archivos_temp_paths)} archivos guardados temporalmente")
                
                # Guardar datos validados en sesión
                validated_data = serializer.validated_data
    
                request.session['denuncia_relacion_id'] = validated_data['relacion_empresa_id']
                request.session['denuncia_relacion'] = RelacionEmpresa.objects.get(
                    id=validated_data['relacion_empresa_id']
                ).rol
                
                if validated_data.get('descripcion_relacion'):
                    request.session['descripcion_relacion'] = validated_data['descripcion_relacion']
                
                request.session['denuncia_tiempo_id'] = validated_data['tiempo_id']
                request.session['denuncia_tiempo'] = Tiempo.objects.get(
                    id=validated_data['tiempo_id']
                ).intervalo
                
                request.session['denuncia_descripcion'] = validated_data['descripcion']
                
                request.session.modified = True
                
                
                return Response({
                    'success': True,
                    'message': 'Información de denuncia procesada',
                    'data': {
                        'relacion': request.session.get('denuncia_relacion'),
                        'tiempo': request.session.get('denuncia_tiempo'),
                        'descripcion': validated_data['descripcion'][:100] + '...',
                        'archivos_count': len(archivos_procesados)
                    },
                    'redirect_url': '/denuncia/Paso3/'
                })
            else:
                print(f"❌ Serializer inválido: {serializer.errors}")
                # Limpiar archivos temporales en caso de error de validación
                if archivos_temp_paths:
                    self._cleanup_temp_files([a['temp_path'] for a in archivos_temp_paths])
                
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=400)
                
        except Exception as e:
            print(f"❌ ERROR EN _process_wizard: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Limpiar archivos temporales en caso de error
            if archivos_temp_paths:
                self._cleanup_temp_files([a['temp_path'] for a in archivos_temp_paths])
            
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}'
            }, status=500)
    
    # ===== PASO 3: REGISTRO DE USUARIO Y CREACIÓN DE DENUNCIA =====
    @transaction.atomic
    def _process_user(self, request):
        """
        Procesa el registro de usuario y crea la denuncia final (Paso 3)
        Recupera archivos temporales, los sube a S3 y los elimina localmente
        """

        archivos_subidos = []  # Para rastrear archivos subidos a S3 en caso de error
        
        try:
            # Verificar sesión
            required_session_keys = [
                'denuncia_item_id',
                'denuncia_relacion_id', 
                'denuncia_tiempo_id',
                'denuncia_descripcion'
            ]
            
            missing_keys = []
            for key in required_session_keys:
                if not request.session.get(key):
                    missing_keys.append(key)
                    print(f"❌ Falta en sesión: {key}")
            
            if missing_keys:
                # Limpiar archivos temporales si la sesión es inválida
                self._cleanup_temp_files_from_session(request)
                
                return Response({
                    'success': False,
                    'message': f'Sesión expirada o datos incompletos. Faltan: {missing_keys}',
                    'redirect': '/denuncia/Paso1/'
                }, status=400)
            
            print("✅ Todos los datos de sesión presentes")
            
            # LÓGICA CORREGIDA: Determinar si es anónimo basándose en datos reales
            # Si hay datos personales (RUT, nombre, correo), la denuncia DEBE ser identificada
            tipo_denuncia = request.data.get('tipo_denuncia', 'anonimo')
            rut = request.data.get('rut', '').strip()
            nombre = request.data.get('nombre_completo', '').strip()
            correo = request.data.get('correo_electronico', '').strip()
            
            # Verificar si realmente hay datos personales
            tiene_datos_personales = bool(rut or nombre or correo)
            
            # Si hay datos personales, NO puede ser anónimo, sin importar el radio button
            es_anonimo = not tiene_datos_personales
            
            # Preparar datos para el serializer
            if es_anonimo:
                # Usuario anónimo solo necesita el flag
                user_data = {
                    'anonimo': True
                }

            else:
                # Usuario identificado necesita todos los campos
                user_data = {
                    'anonimo': False,
                    'rut': rut,
                    'nombre': nombre,
                    'apellidos': request.data.get('apellidos', '').strip(),
                    'correo': correo,
                    'celular': request.data.get('celular', '').strip()
                }
            
            
            
            serializer = UsuarioCreateSerializer(data=user_data)
            
            if serializer.is_valid():
                
                # Usar update_or_create() en lugar de save()
                usuario = serializer.update_or_create()
            
                
                codigo_denuncia = self._generar_codigo_anonimo()
                
                
                # Obtener empresa desde la sesión
                empresa_id = request.session.get('empresa_id')
                if not empresa_id:
                    print("❌ No hay empresa_id en sesión")
                    self._cleanup_temp_files_from_session(request)
                    return Response({
                        'success': False,
                        'message': 'No se encontró la empresa seleccionada',
                        'redirect': '/denuncia/'
                    }, status=400)
                
                # Crear denuncia
                denuncia = Denuncia.objects.create(
                    codigo=codigo_denuncia,
                    tipo_empresa_id=empresa_id,
                    usuario=usuario,
                    item_id=request.session.get('denuncia_item_id'),
                    relacion_empresa_id=request.session.get('denuncia_relacion_id'),
                    tiempo_id=request.session.get('denuncia_tiempo_id'),
                    descripcion=request.session.get('denuncia_descripcion'),
                    descripcion_relacion=request.session.get('descripcion_relacion', ''),
                    estado_actual='PENDIENTE'
                )
                
                request.session['codigo'] = codigo_denuncia
                
                # ===== PROCESAR ARCHIVOS TEMPORALES Y SUBIR A S3 =====
                archivos_guardados = []
                archivos_temp_paths = request.session.get('archivos_temp_paths', [])
                
                if archivos_temp_paths:
                    
                    import boto3
                    from botocore.config import Config
                    
                    s3_client = boto3.client(
                        's3',
                        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        config=Config(signature_version='s3v4')
                    )
                    
                    for archivo_info in archivos_temp_paths:
                        temp_path = archivo_info['temp_path']
                        
                        try:
                            # Verificar que el archivo temporal existe
                            if not os.path.exists(temp_path):
                                print(f"⚠️ Archivo temporal no encontrado: {temp_path}")
                                continue
                            
                            # Leer contenido del archivo
                            with open(temp_path, 'rb') as f:
                                file_content = f.read()
                            
                            # Key: codigo/nombre_archivo
                            s3_key = f"{denuncia.codigo}/{archivo_info['original_name']}"
                            
                            # Subir a S3 con ACL público
                            s3_client.put_object(
                                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                Key=s3_key,
                                Body=file_content,
                                ContentType=archivo_info['type'],
                                ACL='public-read'
                            )
                            
                            archivos_subidos.append(s3_key)
                            
                            # Construir URL pública completa
                            url_publica = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
                            
                            # Crear objeto Archivo en la base de datos
                            archivo_obj = Archivo.objects.create(
                                denuncia=denuncia,
                                nombre=archivo_info['original_name'][:250],
                                descripción=f"Archivo adjunto a denuncia {denuncia.codigo}"[:250],
                                archivo=s3_key,  # Key en S3
                                url=url_publica,  # URL directa
                                Peso=archivo_info['size']  # Tamaño en bytes
                            )
                            
                            archivos_guardados.append(archivo_obj)
                            
                        except Exception as e:
                            print(f"❌ Error procesando archivo {temp_path}: {e}")
                            import traceback
                            traceback.print_exc()
                            # Continuar con los demás archivos
                        
                        finally:
                            # SIEMPRE eliminar archivo temporal después de procesarlo
                            try:
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                                    print(f"🗑️ Archivo temporal eliminado: {temp_path}")
                            except Exception as e:
                                print(f"⚠️ No se pudo eliminar archivo temporal {temp_path}: {e}")
                    
                
                # Limpiar sesión (incluye limpieza adicional de archivos huérfanos)
                self._limpiar_sesion_denuncia(request)
                
                # Preparar respuesta
                response_data = {
                    'success': True,
                    'message': 'Denuncia creada exitosamente',
                    'data': {
                        'codigo': codigo_denuncia,
                        'tipo': 'anónima' if usuario.anonimo else 'identificada',
                        'archivos_count': len(archivos_guardados)
                    },
                    'redirect_url': f'/denuncia/confirmacion/{codigo_denuncia}/'
                }
                
                return Response(response_data, status=201)
                
            else:
                print(f"❌ Serializer de usuario inválido: {serializer.errors}")
                # Limpiar archivos temporales en caso de error de validación
                self._cleanup_temp_files_from_session(request)
                
                return Response({
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'Error en los datos del usuario'
                }, status=400)
                
        except Exception as e:
            print(f"❌ ERROR EN _process_user: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self._cleanup_temp_files_from_session(request)

            if archivos_subidos:
                try:
                    import boto3
                    from botocore.config import Config
                    
                    s3_client = boto3.client(
                        's3',
                        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        config=Config(signature_version='s3v4')
                    )
                    
                    for s3_key in archivos_subidos:
                        try:
                            s3_client.delete_object(
                                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                Key=s3_key
                            )
                            print(f"🗑️ Archivo eliminado de S3: {s3_key}")
                        except Exception as delete_error:
                            print(f"⚠️ No se pudo eliminar {s3_key} de S3: {delete_error}")
                except Exception as cleanup_error:
                    print(f"⚠️ Error en limpieza de S3: {cleanup_error}")
            
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}'
            }, status=500)
    
    # ===== FUNCIÓN DE VALIDACIÓN DE ARCHIVOS =====
    def _validate_file(self, archivo):
        """
        Valida un archivo antes de guardarlo
        
        Args:
            archivo: Archivo Django UploadedFile
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        # Validar tamaño
        if archivo.size > self.MAX_FILE_SIZE:
            return {
                'success': False,
                'message': f'El archivo {archivo.name} excede el tamaño máximo de 500MB'
            }
        
        # Validar extensión
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return {
                'success': False,
                'message': f'Extensión {ext} no permitida para {archivo.name}'
            }
        
        # Validar tipo MIME
        if archivo.content_type not in self.ALLOWED_MIME_TYPES:
            return {
                'success': False,
                'message': f'Tipo de archivo no permitido: {archivo.content_type}'
            }
        
        return {'success': True}
    
    # ===== FUNCIONES DE LIMPIEZA =====
    def _cleanup_temp_files(self, file_paths):
        """
        Elimina archivos temporales dada una lista de rutas
        
        Args:
            file_paths (list): Lista de rutas de archivos a eliminar
        """
        if not file_paths:
            return
        
        for temp_path in file_paths:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"🗑️ Archivo temporal eliminado: {temp_path}")
            except Exception as e:
                print(f"⚠️ Error eliminando archivo temporal {temp_path}: {e}")
    
    def _cleanup_temp_files_from_session(self, request):
        """
        Elimina archivos temporales guardados en la sesión
        
        Args:
            request: Objeto request de Django con sesión
        """
        archivos_temp = request.session.get('archivos_temp_paths', [])
        
        if not archivos_temp:
            return
        
        for archivo in archivos_temp:
            try:
                temp_path = archivo.get('temp_path')
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"🗑️ Archivo temporal eliminado: {temp_path}")
            except Exception as e:
                print(f"⚠️ Error eliminando archivo temporal: {e}")
    
    def _cleanup_orphaned_temp_files(self, max_age_hours=24):
        """
        OPCIONAL: Limpia archivos temporales huérfanos (con prefijo temp_) en MEDIA_ROOT
        Esta función puede ser llamada periódicamente por un cron job o Celery task
        para limpiar archivos que quedaron por procesos interrumpidos.
        
        Args:
            max_age_hours (int): Edad máxima en horas antes de eliminar (default: 24)
        """
        try:
            if not os.path.exists(settings.MEDIA_ROOT):
                return
            
            now = time.time()
            max_age_seconds = max_age_hours * 3600
            files_deleted = 0
            
            # Buscar archivos con prefijo temp_ en MEDIA_ROOT
            for filename in os.listdir(settings.MEDIA_ROOT):
                if not filename.startswith('temp_'):
                    continue
                    
                file_path = os.path.join(settings.MEDIA_ROOT, filename)
                
                try:
                    # Verificar si es un archivo (no directorio)
                    if os.path.isfile(file_path):
                        # Obtener edad del archivo
                        file_age = now - os.path.getmtime(file_path)
                        
                        # Eliminar si es más viejo que max_age
                        if file_age > max_age_seconds:
                            os.remove(file_path)
                            files_deleted += 1
                except Exception as e:
                    print(f"⚠️ Error procesando {filename}: {e}")
            
            if files_deleted > 0:
                print(f"✅ Total archivos temporales huérfanos eliminados: {files_deleted}")
        
        except Exception as e:
            print(f"⚠️ Error en limpieza de archivos temporales huérfanos: {e}")
    
    def _limpiar_sesion_denuncia(self, request):
        """
        Limpia los datos de denuncia de la sesión y archivos temporales
        """
        self._cleanup_temp_files_from_session(request)
        
        keys_to_delete = [
            'denuncia_item_id', 'denuncia_item_nombre', 
            'denuncia_categoria_nombre',
            'denuncia_relacion_id', 'denuncia_relacion',
            'denuncia_tiempo_id', 'denuncia_tiempo',
            'denuncia_descripcion', 'descripcion_relacion',
            'archivos_temp', 'archivos_temp_paths', 'archivos_to_process',
        ]
        
        for key in keys_to_delete:
            request.session.pop(key, None)
        
        request.session.modified = True
    
    # ===== VALIDACIÓN DE RUT =====
    def _validate_rut(self, request):
        """
        Valida un RUT chileno y verifica si existe en la base de datos
        """
        try:
            rut = request.data.get('rut', '').strip()
            
            if not rut:
                return Response({
                    'success': False,
                    'valid': False,
                    'exists': False,
                    'message': 'RUT requerido',
                    'error_type': 'required'
                }, status=400)
            
            
            # Validar formato del RUT usando la función local
            validation_result = validate_rut(rut)
            
            # Verificar que el resultado no sea None
            if validation_result is None or not isinstance(validation_result, tuple):
                return Response({
                    'success': False,
                    'valid': False,
                    'exists': False,
                    'message': 'Error al validar el RUT',
                    'error_type': 'validation_error'
                }, status=500)
            
            is_valid, formatted_rut = validation_result
            
            if not is_valid:
                print(f"❌ RUT inválido: {rut}")
                return Response({
                    'success': False,
                    'valid': False,
                    'exists': False,
                    'message': 'RUT inválido. Por favor verifique el formato',
                    'error_type': 'invalid_format'
                }, status=200)
            
            # Verificar si el RUT existe en la base de datos
            try:
                # Buscar usuario por RUT (solo no anónimos)
                usuario_existente = Usuario.objects.filter(
                    rut__iexact=formatted_rut, 
                    anonimo=False
                ).first()
                
                if usuario_existente:
                    print(f"✅ RUT encontrado en base de datos: ID {usuario_existente.id}")
                    
                    # Preparar información del usuario
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
            # Buscar usuario por RUT (solo no anónimos)
            usuario = Usuario.objects.filter(
                rut__iexact=rut, 
                anonimo=False
            ).first()
            
            if usuario:
                print(f"✅ Usuario encontrado: {usuario.nombre_completo}")
                
                # Preparar datos para autocompletar
                # Separar nombre completo en nombre y apellidos si es necesario
                nombre_completo_parts = usuario.nombre_completo.split(' ', 1)
                nombre = nombre_completo_parts[0] if len(nombre_completo_parts) > 0 else ''
                apellidos = nombre_completo_parts[1] if len(nombre_completo_parts) > 1 else ''
                
                # Si el usuario tiene campos separados, usarlos
                if hasattr(usuario, 'nombre') and usuario.nombre:
                    nombre = usuario.nombre
                if hasattr(usuario, 'apellidos') and usuario.apellidos:
                    apellidos = usuario.apellidos
                
                autocomplete_data = {
                    'nombre_completo': usuario.nombre_completo,
                    'nombre': nombre,
                    'apellidos': apellidos,
                    'correo_electronico': usuario.correo if usuario.correo else '',
                    'celular': usuario.celular.replace('+569', '') if usuario.celular else ''
                }
                
                print(f"Datos de autocompletado: {autocomplete_data}")
                
                return Response({
                    'success': True,
                    'found': True,
                    'autocomplete_data': autocomplete_data,
                    'message': 'Datos encontrados y autocompletados'
                })
            else:
                print("❌ Usuario no encontrado o es anónimo")
                return Response({
                    'success': True,
                    'found': False,
                    'message': 'No se encontraron datos para autocompletar'
                })
                
        except Exception as e:
            print(f"❌ Error al buscar usuario: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error al buscar datos del usuario',
                'error': str(e)
            }, status=500)
    
    # ===== CONSULTA DE DENUNCIA =====
    def _consulta_denuncia(self, request):
        """
        Consultar estado de denuncia por código
        Ahora todos los códigos son DN-XXXXX (tanto anónimos como identificados)
        """
        codigo = request.data.get('codigo', '').strip().upper()
        
        if not codigo:
            return Response({
                'success': False,
                'message': 'Código requerido'
            }, status=400)
        
        # Validar formato DN-XXXXX
        if not codigo.startswith('DN-'):
            return Response({
                'success': False,
                'message': 'Formato de código inválido. Debe ser DN-XXXXX'
            }, status=400)
        
        # Buscar denuncia por código (funciona para anónimos e identificados)
        denuncias = Denuncia.objects.filter(codigo=codigo)
        
        if denuncias.exists():
            denuncia = denuncias.first()
            usuario = denuncia.usuario
            
            # Determinar tipo de denuncia
            es_anonima = usuario.anonimo
            tipo_consulta = 'anonima' if es_anonima else 'identificada'
            
            # Preparar datos para la sesión
            request.session['codigo_consulta'] = codigo
            request.session['tipo_consulta'] = tipo_consulta
            if not es_anonima:
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