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
        Obtiene el detalle completo de una denuncia
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
            
            # Serializar datos
            data = {
                'codigo': denuncia.codigo,
                'fecha': denuncia.fecha.isoformat(),
                'categoria': denuncia.item.categoria.nombre,
                'tipo_denuncia': denuncia.item.enunciado,
                'descripcion': denuncia.descripcion,
                'usuario': denuncia.usuario.nombre_completo if not denuncia.usuario.anonimo else 'Anónimo',
                'estado': denuncia.estado_actual,
                'relacion_empresa': denuncia.relacion_empresa.rol,
                'tiempo': denuncia.tiempo.intervalo
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
                    'admin_nombre': m.admin.nombre if m.admin else None,
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
        print("enviar mensaje")
        """
        POST /api/denuncia-envio-mensaje/
        envia el mensaje hacia Foro
        """
        try:
            print("denuncia?")
         
            denuncia= request.data['denuncia_codigo']
           
            mensaje=request.data['mensaje']
            
            print(denuncia)
            print(mensaje)

            # Obtener mensajes del foro
            mensaje_foro=Foro.objects.create(
                denuncia=denuncia,
                mensaje=mensaje,
                leido=False
            )

            print("hola ")

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
            
            # Verificar permisos de admin
            has_permission, categoria = self.check_admin_permissions(request)
            if not has_permission:
                return Response({
                    'success': False,
                    'message': 'Sin permisos de administración'
                }, status=403)
            
            # Obtener datos
            data = json.loads(request.body)
            denuncia_id = data.get('denuncia_id')
            nuevo_estado_id = data.get('nuevo_estado')
            
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
                fecha=datetime.now()
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
            print(request.data)
            denuncia_codigo=request.data.denuncia

            # Aquí deberías implementar la generación del PDF
            # Por ahora, retornamos un PDF dummy
            pdf_content = self._generar_pdf_denuncia(denuncia_codigo)
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="denuncia_{codigo}.pdf"'
            
            return response
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    def _generar_pdf_denuncia(self, denuncia_codigo):
        """
        Método helper para generar el PDF
        Aquí deberías usar una librería como ReportLab o WeasyPrint
        """
        denuncia = Denuncia.objects.get(codigo=denuncia_codigo).first()
        path_archive= './templates/word/template_denuncia.docx'
        # Genero el documento
       
        doc = DocxTemplate(path_archive)
        # Variables de Autorización Firma Electrónica
        context = { 'fecha_descarga':datetime.datetime.now(),
                    'usuario_nombre': denuncia.usuario.nombre,
                    'usuario_apellidos': denuncia.usuario.apellidos,
                    'rol':denuncia.item.categoria.nombre,
                    'codigo': denuncia.codigo,
                    'fecha_denuncia': denuncia.fecha,
                    'item_enunciado': denuncia.item.enunciado,
                    'rol_empresa': denuncia.relación_empresa.rol,
                    'descripcion_relacion': denuncia.descripcion_relacion,
                    'correo_trabajador': denuncia.email,
                    'tiempo': denuncia.tiempo.intervalo,
                    
                    }
            # Creo documento word con datos de trabajador
        doc.render(context)
        path_doc ='Informe_denuncia.docx'
            
            # Guarda el documento
        doc.save(path_doc)


            # Convierto documento a PDF
        pdf = Popen(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir',
                        '', path_doc])
        pdf.communicate()

        path_pdf = 'Informe_denuncia.pdf'
            # Elimino el documento word.
        #os.remove(path_doc)
            # Inicio integración de la API
        #if enviar_autorizacion(request, trabajador, empresas, path_pdf):        
            # ENVIADO_FIRMAR = 'EF' FIRMADO = 'FF' RECHAZADO ='RC' EXPIRADO = 'EX'
        #    trabajador.autorizacion = Trabajador.ENVIADO_FIRMAR
        #    trabajador.save()
        #    messages.success(request, 'Autorización de Firma Electrónica enviada Exitosamente')
        #else:
        #    messages.error(request, 'El documento no se logró enviar a firma')

            # Elimino el documento pdf.
        #os.remove(path_pdf)
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