# service_consolidated.py - APIs consolidadas para operaciones de denuncias
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Denuncia, DenunciaEstado, EstadosDenuncia, Foro, AdminDenuncias
import json
from subprocess import Popen
import os
from datetime import datetime
from docxtpl import DocxTemplate
import datetime
import os
import tempfile
from subprocess import Popen, PIPE


@method_decorator(csrf_exempt, name='dispatch')
class DenunciaManagementViewSet(ViewSet):
    """
    ViewSet consolidado para todas las operaciones relacionadas con denuncias.
    Esto reemplaza las 5 APIViews separadas por una sola clase con múltiples acciones.
    """
    
    def get_denuncia(self, codigo):
        """Helper para obtener denuncia por código"""
        return get_object_or_404(Denuncia, codigo=codigo)
    
    def check_admin_permissions(self, request):
        """Verificar permisos de admin"""
        if not request.user.is_authenticated:
            return False, "Usuario no autenticado"
        
        if request.user.is_superuser:
            return True, None
        
        if hasattr(request.user, 'rol_categoria') and request.user.rol_categoria:
            return True, request.user.rol_categoria
        
        return False, "Usuario sin permisos de administración"

    @action(detail=True, methods=['get'])
    def detalle(self, request, codigo=None):
        """
        GET /api/denuncias/{codigo}/detalle/
        Obtiene el detalle completo de una denuncia incluyendo archivos
        """
        try:
            denuncia = self.get_denuncia(codigo)
            
            if request.user.is_authenticated:
                has_permission, categoria = self.check_admin_permissions(request)
                if not has_permission:
                    return Response({'error': 'Sin permisos'}, status=403)
                
                if categoria and denuncia.item.categoria != categoria:
                    return Response({'error': 'Sin permisos para esta categoría'}, status=403)
            
            archivos = denuncia.archivo_set.all()
            
            data = {
                'codigo': denuncia.codigo,
                'fecha': denuncia.fecha.isoformat(),
                'categoria': denuncia.item.categoria.nombre,
                'tipo_denuncia': denuncia.item.enunciado,
                'descripcion': denuncia.descripcion,
                'descripcion_relacion': denuncia.descripcion_relacion or '',
                'usuario': denuncia.usuario.nombre_completo if not denuncia.usuario.anonimo else 'Anónimo',
                'usuario_anonimo': denuncia.usuario.anonimo,
                'estado': denuncia.estado_actual,
                'relacion_empresa': denuncia.relacion_empresa.rol,
                'tiempo': denuncia.tiempo.intervalo,
                'empresa': denuncia.tipo_empresa.nombre,
                'archivos': [{
                    'id': archivo.id,
                    'nombre': archivo.nombre,
                    'descripcion': archivo.descripción,
                    'peso': archivo.Peso,
                    'url_relativa': archivo.url
                } for archivo in archivos],
                'total_archivos': archivos.count()
            }
            
            return Response(data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    # 2. MENSAJE DE DENUNCIA (reemplaza DenunciaMensajeAPIView)
    @action(detail=True, methods=['get'])
    def mensaje(self, request, codigo=None):
        """
        GET /api/denuncias/{codigo}/mensaje/
        Obtiene los mensajes del foro de una denuncia
        """
        try:
            denuncia = self.get_denuncia(codigo)
            
            mensajes = denuncia.foro_set.all().order_by('id')
          
            data = {
                'codigo': denuncia.codigo,
                'fecha': denuncia.fecha.isoformat(),
                'mensaje': mensajes.first().mensaje if mensajes.exists() else 'Sin mensajes',
                'mensajes': [{
                    'id': m.id,
                    'mensaje': m.mensaje,
                    'es_admin': m.admin is not None,
                    'admin_nombre': m.admin.username if m.admin else None,
                    'fecha':m.fecha,
                } for m in mensajes]
            }
        
            
            return Response(data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=True, methods=['get'])
    def info(self, request, codigo=None):
        """
        GET /api/denuncias/{codigo}/info/
        Obtiene información básica de una denuncia
        """
        try:
            denuncia = self.get_denuncia(codigo)
            
            data = {
                'codigo': denuncia.codigo,
                'fecha': denuncia.fecha.isoformat(),
                'categoria': denuncia.item.categoria.nombre
            }
            
            return Response(data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        

    @action(detail=True, methods=['post'])
    def enviar_mensaje(self, request):
        """
        POST /api/denuncia-envio-mensaje/
        envia el mensaje hacia Foro
        """
        try:
         
            denuncia= request.data['denuncia_codigo']
            mensaje=request.data['mensaje']

            # Obtener mensajes del foro
            mensaje_foro=Foro.objects.create(
                denuncia_id=denuncia,
                admin_id=request.user.id or None,
                mensaje=mensaje,
                leido=False
            )

            mensaje_foro.save()

            data = {
                'success':True,
                'response': "emvio correcto del mensaje",
                'fecha': mensaje_foro.fecha
            }
            
            return Response(data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)


    @action(detail=False, methods=['post'])
    def cambiar_estado(self, request):
        """
        POST /api/denuncias/cambiar-estado/
        Cambia el estado de una denuncia (solo admin)
        """
        try:
            # Verificar autenticación
            if not request.user.is_authenticated:
                return Response({
                    'success': False,
                    'message': 'Usuario no autenticado'
                }, status=401)
            
          
            has_permission, categoria = self.check_admin_permissions(request)
           
            if not has_permission:
                return Response({
                    'success': False,
                    'message': 'Sin permisos de administración'
                }, status=403)
            
           
            
            denuncia_id = request.data.get('denuncia_id')
            nuevo_estado_id = request.data.get('nuevo_estado')
            
            if not denuncia_id or not nuevo_estado_id:
                return Response({
                    'success': False,
                    'message': 'Faltan parámetros requeridos'
                }, status=400)
            
            denuncia = self.get_denuncia(denuncia_id)
            
            if categoria and denuncia.item.categoria != categoria:
                return Response({
                    'success': False,
                    'message': 'Sin permisos para esta categoría de denuncia'
                }, status=403)
            
            try:
                nuevo_estado = DenunciaEstado.objects.get(id=int(nuevo_estado_id))
            except DenunciaEstado.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Estado no válido'
                }, status=400)

            denuncia.estado_actual = nuevo_estado.estado
            denuncia.save()
            
            EstadosDenuncia.objects.create(
                denuncia=denuncia,
                estado=nuevo_estado,
            )
            
            return Response({
                'success': True,
                'message': 'Estado actualizado correctamente',
                'nuevo_estado': nuevo_estado.estado
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al cambiar estado: {str(e)}'
            }, status=500)


    @action(detail=True, methods=['post'])
    def descargar(self, request, codigo=None):
        """
        POST /api/denuncias/{codigo}/descargar/
        Genera y descarga un PDF con la información de la denuncia
        """
        try:
           
            denuncia_codigo=request.data['denuncia_id']
            pdf_content = self._generar_pdf_denuncia(denuncia_codigo)
            return pdf_content
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    def _generar_pdf_denuncia(self, denuncia_codigo):
        """
        Método helper para generar el PDF - CORREGIDO
        """
        try:
            denuncia = Denuncia.objects.filter(codigo=denuncia_codigo).first()
            if not denuncia:
                raise ValueError(f"No se encontró denuncia con código: {denuncia_codigo}")
            
            base_path = os.path.join(os.path.dirname(__file__), 'templates', 'word')
            template_filename = f'template_denuncia_{denuncia.tipo_empresa.nombre}.docx'
            path_archive = os.path.join(base_path, template_filename)
            
            # Generar el documento
            doc = DocxTemplate(path_archive)
            
            context = {
                'fecha_descarga': datetime.datetime.now().strftime('%d/%m/%Y'),
                'rol': denuncia.item.categoria.nombre,
                'codigo': denuncia.codigo,
                'fecha_denuncia': denuncia.fecha.strftime('%d/%m/%Y'),
                'usuario_nombre': denuncia.usuario.nombre or '',
                'usuario_apellidos': denuncia.usuario.apellidos or '',   
                'usuario_celular': denuncia.usuario.celular or '',
                'usuario_correo': denuncia.usuario.correo or '',
                'item_enunciado': denuncia.item.enunciado,
                'rol_empresa': denuncia.relacion_empresa.rol,
                'descripcion': denuncia.descripcion,
                'descripcion_relacion': denuncia.descripcion_relacion or '',
                'correo_trabajador': denuncia.usuario.correo or '',
                'tiempo': denuncia.tiempo.intervalo,
                'archivos': [],
                'anonimo': 'Sí' if denuncia.usuario.anonimo else 'No'
            }
            
            doc.render(context)
            
            temp_dir = tempfile.gettempdir() 
            
           
            path_doc = os.path.join(temp_dir, f'Informe_denuncia_{denuncia_codigo}.docx')
            doc.save(path_doc)
            pdf_process = Popen([
                'libreoffice', 
                '--headless', 
                '--convert-to', 'pdf', 
                '--outdir', temp_dir, 
                path_doc
            ], stdout=PIPE, stderr=PIPE)
            
            stdout, stderr = pdf_process.communicate()
            
            if pdf_process.returncode != 0:
                print(f"Error en conversión PDF: {stderr.decode()}")
                raise Exception(f"Error al convertir a PDF: {stderr.decode()}")
            
            path_pdf = os.path.join(temp_dir, f'Informe_denuncia_{denuncia_codigo}.pdf')
            
            if not os.path.exists(path_pdf):
                raise FileNotFoundError(f"No se encontró el PDF generado en: {path_pdf}")
            
            with open(path_pdf, 'rb') as pdf_file:
                response = HttpResponse(
                    pdf_file.read(), 
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="Informe_denuncia_{denuncia_codigo}.pdf"'
        
            try:
                os.remove(path_doc)
                os.remove(path_pdf)
            except:
                pass 
            
            return response
            
        except Exception as e:
            print(f"ERROR en _generar_pdf_denuncia: {str(e)}")
            raise
    
    @action(detail=False, methods=['get'])
    def descargar_archivo(self, request):
        """
        GET /api/descargar-archivo/?archivo_id=123
        Descarga un archivo específico de una denuncia desde S3
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            from django.conf import settings
            import mimetypes
            
            archivo_id = request.GET.get('archivo_id')
            
            if not archivo_id:
                return Response({'error': 'ID de archivo requerido'}, status=400)
            
            
            try:
                from .models import Archivo
                archivo = Archivo.objects.select_related('denuncia').get(id=archivo_id)
            except Archivo.DoesNotExist:
                return Response({'error': 'Archivo no encontrado'}, status=404)
            
            
            if request.user.is_authenticated:
                has_permission, categoria = self.check_admin_permissions(request)
                if not has_permission:
                    return Response({'error': 'Sin permisos'}, status=403)
                
                if categoria and archivo.denuncia.item.categoria != categoria:
                    return Response({'error': 'Sin permisos para esta categoría'}, status=403)
            
           
            if archivo.archivo:
                s3_key = archivo.archivo.name
            else:
                archivo_url = archivo.url
                if settings.AWS_S3_CUSTOM_DOMAIN in archivo_url:
                    s3_key = archivo_url.split(settings.AWS_S3_CUSTOM_DOMAIN + '/')[-1]
                elif archivo_url.startswith('https://'):
                    s3_key = archivo_url.split('/')[-2] + '/' + archivo_url.split('/')[-1]
                elif archivo_url.startswith('/media/'):
                    s3_key = archivo_url[7:]
                elif archivo_url.startswith('media/'):
                    s3_key = archivo_url[6:]
                else:
                    s3_key = archivo_url
            
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            try:
                s3_response = s3_client.get_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=s3_key
                )
                
                
                file_content = s3_response['Body'].read()
                
                print(f"✅ Archivo descargado exitosamente ({len(file_content)} bytes)")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"❌ Error de S3 ({error_code}): {str(e)}")
                
                if error_code == 'NoSuchKey':
                    return Response({
                        'error': 'Archivo no encontrado en el almacenamiento',
                        'details': f'Key: {s3_key}'
                    }, status=404)
                else:
                    return Response({
                        'error': f'Error al acceder al almacenamiento: {error_code}',
                        'details': str(e)
                    }, status=500)
            
            mime_type = s3_response.get('ContentType')
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(archivo.nombre)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            response = HttpResponse(file_content, content_type=mime_type)
            response['Content-Disposition'] = f'attachment; filename="{archivo.nombre}"'
            response['Content-Length'] = len(file_content)
            
            return response
        
        except Exception as e:
            print(f"❌ ERROR GENERAL en descargar_archivo: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'Error al descargar archivo: {str(e)}'
            }, status=500)
     
    @action(detail=False, methods=['post'])
    def agregar_archivos(self, request):
        """
        POST /api/denuncias/agregar_archivos/
        Permite a los administradores agregar archivos a una denuncia existente
        """
        try:
            from django.conf import settings
            from .models import Archivo
            import os
            import uuid
            import boto3
            from botocore.config import Config
            
            has_permission, categoria = self.check_admin_permissions(request)
            if not has_permission:
                return Response({
                    'success': False,
                    'message': 'No tiene permisos para agregar archivos'
                }, status=403)
            
            denuncia_codigo = request.data.get('denuncia_codigo')
            archivos = request.FILES.getlist('archivos[]')
            
            if not denuncia_codigo:
                return Response({
                    'success': False,
                    'message': 'Código de denuncia requerido'
                }, status=400)
            
            if not archivos or len(archivos) == 0:
                return Response({
                    'success': False,
                    'message': 'No se recibieron archivos'
                }, status=400)
            
            try:
                denuncia = Denuncia.objects.get(codigo=denuncia_codigo)
            except Denuncia.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Denuncia {denuncia_codigo} no encontrada'
                }, status=404)
            
            if categoria and denuncia.item.categoria != categoria:
                return Response({
                    'success': False,
                    'message': 'No tiene permisos para modificar esta categoría'
                }, status=403)
            
        
            MAX_FILE_SIZE = 500 * 1024 * 1024  
            ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.xlsx', '.xls', '.txt'}
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
            
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=Config(signature_version='s3v4')
            )
            
            archivos_subidos = []
            errores = []
            
            for archivo in archivos:
                try:
        
                    if archivo.size > MAX_FILE_SIZE:
                        errores.append(f'{archivo.name}: Excede el tamaño máximo (500MB)')
                        continue
                    

                    ext = os.path.splitext(archivo.name)[1].lower()
                    if ext not in ALLOWED_EXTENSIONS:
                        errores.append(f'{archivo.name}: Extensión no permitida')
                        continue
                    
                    if archivo.content_type not in ALLOWED_MIME_TYPES:
                        errores.append(f'{archivo.name}: Tipo de archivo no permitido')
                        continue
                    
                    nombre_unico = f"{uuid.uuid4()}_{archivo.name}"
                    s3_key = f"{denuncia.codigo}/{nombre_unico}"
                    
                    file_content = archivo.read()
                    
                    
                    s3_client.put_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=s3_key,
                        Body=file_content,
                        ContentType=archivo.content_type,
                        ACL='public-read'
                    )
                    

                    url_publica = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
                    
                  
                    archivo_obj = Archivo.objects.create(
                        denuncia=denuncia,
                        nombre=archivo.name[:250],
                        descripción=f"Archivo agregado por admin {request.user.username}"[:250],
                        archivo=s3_key,
                        url=url_publica,
                        Peso=archivo.size
                    )
                    
                    archivos_subidos.append({
                        'id': archivo_obj.id,
                        'nombre': archivo_obj.nombre,
                        'url': url_publica,
                        'peso': archivo.size
                    })
                    
                    
                except Exception as e:
                    error_msg = f'{archivo.name}: {str(e)}'
                    errores.append(error_msg)
                    print(f"❌ Error subiendo {archivo.name}: {str(e)}")
            
            if len(archivos_subidos) > 0:
                mensaje = f'{len(archivos_subidos)} archivo(s) subido(s) correctamente'
                if errores:
                    mensaje += f'. {len(errores)} archivo(s) con errores'
                
                return Response({
                    'success': True,
                    'message': mensaje,
                    'archivos_subidos': len(archivos_subidos),
                    'archivos': archivos_subidos,
                    'errores': errores if errores else None
                })
            else:
                return Response({
                    'success': False,
                    'message': 'No se pudo subir ningún archivo',
                    'errores': errores
                }, status=400)
            
        except Exception as e:
            print(f"❌ Error en agregar_archivos: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}'
            }, status=500)
            

class DenunciaQueryAPI(APIView):
    """
    API consolidada para diferentes tipos de consultas de denuncias
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, action=None):
        """
        POST /api/denuncias/query/{action}/
        
        Acciones disponibles:
        - by_code: Buscar por código
        - by_user: Buscar por usuario
        - by_category: Buscar por categoría
        - stats: Obtener estadísticas
        """
        try:
            data = json.loads(request.body) if request.body else {}
            
            if action == 'by_code':
                return self._query_by_code(data)
            elif action == 'by_user':
                return self._query_by_user(data)
            elif action == 'by_category':
                return self._query_by_category(data)
            elif action == 'stats':
                return self._get_stats(data)
            else:
                return JsonResponse({
                    'error': f'Acción no válida: {action}'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    def _query_by_code(self, data):
        """Buscar denuncias por código"""
        codigo = data.get('codigo', '').upper()
        
        if not codigo:
            return JsonResponse({'error': 'Código requerido'}, status=400)
        
        try:
            if codigo.startswith('DN-'):
                denuncias = Denuncia.objects.filter(codigo=codigo)
            else:
                denuncias = Denuncia.objects.filter(usuario__id=codigo)
            
            results = [{
                'codigo': d.codigo,
                'fecha': d.fecha.isoformat(),
                'estado': d.estado_actual,
                'categoria': d.item.categoria.nombre
            } for d in denuncias]
            
            return JsonResponse({
                'success': True,
                'count': len(results),
                'results': results
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _query_by_user(self, data):
        """Buscar denuncias por usuario"""
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({'error': 'ID de usuario requerido'}, status=400)
        
        denuncias = Denuncia.objects.filter(usuario__id=user_id)
        
        results = [{
            'codigo': d.codigo,
            'fecha': d.fecha.isoformat(),
            'estado': d.estado_actual,
            'categoria': d.item.categoria.nombre
        } for d in denuncias]
        
        return JsonResponse({
            'success': True,
            'count': len(results),
            'results': results
        })
    
    def _query_by_category(self, data):
        """Buscar denuncias por categoría"""
        categoria_id = data.get('categoria_id')
        
        if not categoria_id:
            return JsonResponse({'error': 'ID de categoría requerido'}, status=400)
        
        denuncias = Denuncia.objects.filter(item__categoria__id=categoria_id)
        
        results = [{
            'codigo': d.codigo,
            'fecha': d.fecha.isoformat(),
            'estado': d.estado_actual,
            'tipo': d.item.enunciado
        } for d in denuncias]
        
        return JsonResponse({
            'success': True,
            'count': len(results),
            'results': results
        })