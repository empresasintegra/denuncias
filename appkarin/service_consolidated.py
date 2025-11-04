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
        
        # Si es superuser, tiene todos los permisos
        if request.user.is_superuser:
            return True, None
        
        # Si tiene rol_categoria, puede ver/editar solo esas denuncias
        if hasattr(request.user, 'rol_categoria') and request.user.rol_categoria:
            return True, request.user.rol_categoria
        
        return False, "Usuario sin permisos de administración"

    # 1. DETALLE DE DENUNCIA (reemplaza DenunciaDetalleAPIView)
    @action(detail=True, methods=['get'])
    def detalle(self, request, codigo=None):
        """
        GET /api/denuncias/{codigo}/detalle/
        Obtiene el detalle completo de una denuncia incluyendo archivos
        """
        try:
            denuncia = self.get_denuncia(codigo)
            
            # Verificar permisos
            if request.user.is_authenticated:
                has_permission, categoria = self.check_admin_permissions(request)
                if not has_permission:
                    return Response({'error': 'Sin permisos'}, status=403)
                
                # Si tiene categoría específica, verificar que coincida
                if categoria and denuncia.item.categoria != categoria:
                    return Response({'error': 'Sin permisos para esta categoría'}, status=403)
            
            # ✅ NUEVO: Obtener archivos de la denuncia
            archivos = denuncia.archivo_set.all()
            
            # Serializar datos
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
                # ✅ NUEVO: Incluir archivos
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
            
            # Obtener mensajes del foro
            mensajes = denuncia.foro_set.all().order_by('id')
            print(mensajes)
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
            print(data)
            
            return Response(data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    # 3. INFORMACIÓN BÁSICA (reemplaza DenunciaInfoAPIView)
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


    # 4. CAMBIAR ESTADO (reemplaza CambiarEstadoDenunciaAPIView)
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
            
            print("permison?")
            # Verificar permisos de admin
            has_permission, categoria = self.check_admin_permissions(request)
            print("permison2?")
            if not has_permission:
                return Response({
                    'success': False,
                    'message': 'Sin permisos de administración'
                }, status=403)
            
            # Obtener datos
            
            denuncia_id = request.data.get('denuncia_id')
            nuevo_estado_id = request.data.get('nuevo_estado')
            
            if not denuncia_id or not nuevo_estado_id:
                return Response({
                    'success': False,
                    'message': 'Faltan parámetros requeridos'
                }, status=400)
            
            # Obtener denuncia
            denuncia = self.get_denuncia(denuncia_id)
            
            # Verificar permisos sobre la categoría
            if categoria and denuncia.item.categoria != categoria:
                return Response({
                    'success': False,
                    'message': 'Sin permisos para esta categoría de denuncia'
                }, status=403)
            
            # Obtener el nuevo estado
            try:
                nuevo_estado = DenunciaEstado.objects.get(id=int(nuevo_estado_id))
            except DenunciaEstado.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Estado no válido'
                }, status=400)
            
            # Actualizar estado
            denuncia.estado_actual = nuevo_estado.estado
            denuncia.save()
            
            # Registrar en historial
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

    # 5. DESCARGAR PDF (reemplaza DescargarDenunciaAPIView)
    @action(detail=True, methods=['post'])
    def descargar(self, request, codigo=None):
        """
        POST /api/denuncias/{codigo}/descargar/
        Genera y descarga un PDF con la información de la denuncia
        """
        try:
           
            denuncia_codigo=request.data['denuncia_id']
            # Aquí deberías implementar la generación del PDF
            # Por ahora, retornamos un PDF dummy
            pdf_content = self._generar_pdf_denuncia(denuncia_codigo)
            print("pdf_content",pdf_content)
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
            
            # ✅ SOLUCIÓN: Usar directorio temporal
            temp_dir = tempfile.gettempdir()  # O usar tempfile.mkdtemp() para un dir único
            
            # Guardar el documento Word en directorio temporal
            path_doc = os.path.join(temp_dir, f'Informe_denuncia_{denuncia_codigo}.docx')
            doc.save(path_doc)
            
            # ✅ CORREGIDO: Especificar correctamente el directorio de salida
            pdf_process = Popen([
                'libreoffice', 
                '--headless', 
                '--convert-to', 'pdf', 
                '--outdir', temp_dir,  # ✅ Directorio temporal en lugar de ''
                path_doc
            ], stdout=PIPE, stderr=PIPE)
            
            # Esperar a que termine el proceso y capturar salida
            stdout, stderr = pdf_process.communicate()
            
            # Verificar si hubo errores
            if pdf_process.returncode != 0:
                print(f"Error en conversión PDF: {stderr.decode()}")
                raise Exception(f"Error al convertir a PDF: {stderr.decode()}")
            
            # El PDF tendrá el mismo nombre pero con extensión .pdf
            path_pdf = os.path.join(temp_dir, f'Informe_denuncia_{denuncia_codigo}.pdf')
            
            # Verificar que el PDF se creó
            if not os.path.exists(path_pdf):
                raise FileNotFoundError(f"No se encontró el PDF generado en: {path_pdf}")
            
            # Leer el PDF
            with open(path_pdf, 'rb') as pdf_file:
                response = HttpResponse(
                    pdf_file.read(), 
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="Informe_denuncia_{denuncia_codigo}.pdf"'
            
            # Limpiar archivos temporales
            try:
                os.remove(path_doc)
                os.remove(path_pdf)
            except:
                pass  # Si falla la limpieza, no es crítico
            
            return response
            
        except Exception as e:
            print(f"ERROR en _generar_pdf_denuncia: {str(e)}")
            raise
    
    @action(detail=False, methods=['get'])
    def descargar_archivo(self, request):
        """
        GET /api/descargar-archivo/?archivo_id=123
        Descarga un archivo específico de una denuncia
        """
        try:
            from django.http import FileResponse
            from django.conf import settings
            import os
            import mimetypes
            
            archivo_id = request.GET.get('archivo_id')
            
            if not archivo_id:
                return Response({'error': 'ID de archivo requerido'}, status=400)
            
            # Obtener archivo con su denuncia
            try:
                from .models import Archivo
                archivo = Archivo.objects.select_related('denuncia').get(id=archivo_id)
            except Archivo.DoesNotExist:
                return Response({'error': 'Archivo no encontrado'}, status=404)
            
            # Verificar permisos
            if request.user.is_authenticated:
                has_permission, categoria = self.check_admin_permissions(request)
                if not has_permission:
                    return Response({'error': 'Sin permisos'}, status=403)
                
                if categoria and archivo.denuncia.item.categoria != categoria:
                    return Response({'error': 'Sin permisos para esta categoría'}, status=403)
            
            # ✅ SOLUCIÓN: Limpiar la URL antes de construir la ruta
            archivo_url = archivo.url
            
            # Si la URL empieza con /media/, quitarlo
            if archivo_url.startswith('/media/'):
                archivo_url = archivo_url[7:]  # Quitar '/media/'
            elif archivo_url.startswith('media/'):
                archivo_url = archivo_url[6:]  # Quitar 'media/'
            
            # Ahora construir la ruta correcta
            file_path = os.path.join(settings.MEDIA_ROOT, archivo_url)
            
            # ✅ DEBUG: Imprimir rutas para verificar
            print(f"DEBUG - archivo.url original: {archivo.url}")
            print(f"DEBUG - archivo_url limpia: {archivo_url}")
            print(f"DEBUG - MEDIA_ROOT: {settings.MEDIA_ROOT}")
            print(f"DEBUG - file_path final: {file_path}")
            print(f"DEBUG - archivo existe: {os.path.exists(file_path)}")
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                return Response({
                    'error': f'Archivo no encontrado en el sistema: {file_path}'
                }, status=404)
            
            # Detectar tipo MIME
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Servir archivo
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=mime_type,
                as_attachment=True,
                filename=archivo.nombre
            )
            
            return response
        
        except Exception as e:
            print(f"ERROR en descargar_archivo: {str(e)}")
            return Response({'error': f'Error al descargar archivo: {str(e)}'}, status=500)
        #eliminar_qr(url)
            
    #return redirect('users:list-trabajador')


# También puedes crear una API consolidada para operaciones de consulta
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
                # Denuncia anónima
                denuncias = Denuncia.objects.filter(codigo=codigo)
            else:
                # Usuario identificado
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
    
    def _get_stats(self, data):
        """Obtener estadísticas de denuncias"""
        from django.db.models import Count
        
        # Estadísticas por estado
        estados = Denuncia.objects.values('estado_actual').annotate(
            total=Count('id')
        )
        
        # Estadísticas por categoría
        categorias = Denuncia.objects.values(
            'item__categoria__nombre'
        ).annotate(
            total=Count('id')
        )
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total': Denuncia.objects.count(),
                'por_estado': list(estados),
                'por_categoria': list(categorias)
            }
        })