# service_datatable_simple.py - API simplificada para DataTable de Denuncias
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from .models import Denuncia, Usuario, AdminDenuncias,Foro
import json


@method_decorator(csrf_exempt, name='dispatch')
class SimpleDenunciaDataTableAPIView(APIView):
    """
    API simplificada para DataTable de denuncias
    Maneja 4 tipos de usuarios:
    - Anónimo (DN-XXXXXX)
    - Identificado (XXXXX)
    - Admin por categoría (request.user con categoría)
    - Super admin
    """
    
    def post(self, request, *args, **kwargs):
        try:
            # Parsear datos de DataTables
            dt_data = self._parse_datatable_request(request)

            admin = AdminDenuncias.objects.filter(id=request.user.id).first()

            # ✅ FORMA CORRECTA con Count y filtros
            denuncia = Denuncia.objects.select_related(
                'usuario',
                'item', 
                'item__categoria',
                'relacion_empresa',
                'tiempo'
            ).annotate(
                num_archivos=Count('archivo'),
                
                # ✅ Contar mensajes NO leídos del admin específico
                num_mensajes_no_leidos=Count(
                    'foro',
                    filter=Q(foro__leido=False, foro__admin=admin)
                ),
                
                # ✅ Contar mensajes SÍ leídos del admin específico  
                num_mensajes_leidos=Count(
                    'foro',
                    filter=Q(foro__leido=True, foro__admin=admin)
                ),
                
                # ✅ Contar TODOS los mensajes del admin
                num_mensajes_total=Count(
                    'foro',
                    filter=Q(foro__admin=admin)
                )
            )
            
            # FILTRADO DIRECTO por usuario autenticado
            if request.user.is_authenticated:
                # Usuario admin autenticado
                print("estoy autenticado")
                print(request.user.rol_categoria.nombre)

                if request.user.rol_categoria:
                    # Admin con categoría específica: solo denuncias de su categoría
                    print(f"Admin autenticado - Filtrando por categoría: {request.user.rol_categoria.nombre} (ID: {request.user.rol_categoria.id})")
                    denuncia = denuncia.filter(item__categoria_id=request.user.rol_categoria.id)
            else:
                # Usuarios no autenticados (consultas por código)
                user_info = dt_data.get('user_info', {})
                user_type = user_info.get('tipo', 'guest')
                codigo = user_info.get('codigo', '')
                
                if user_type == 'anonimo' and codigo:
                    # Usuario anónimo: filtrar por código
                    print(f"Usuario anónimo - Código: {codigo}")
                    denuncia = denuncia.filter(codigo=codigo)
                elif user_type == 'identificado' and codigo:
                    # Usuario identificado: filtrar por ID de usuario
                    print(f"Usuario identificado - ID: {codigo}")
                    denuncia = denuncia.filter(usuario__id=codigo)
                else:
                    # Sin permisos - no mostrar nada
                    print("Sin permisos - Sin denuncias")
                    denuncia = denuncia.none()
            
            # Aplicar búsqueda si existe
            search_value = dt_data.get('search', {}).get('value', '')
            if search_value:
                denuncia = self._apply_search(denuncia, search_value)
            
            # Contar registros
            records_filtered = denuncia.count()
            
            # Aplicar ordenamiento
            denuncia = self._apply_ordering(denuncia, dt_data)
            
            # Paginar
            start = dt_data.get('start', 0)
            length = dt_data.get('length', 10)
            denuncias = denuncia[start:start + length]
            
            # Serializar datos
            data = []
            for denuncia in denuncias:
                data.append({
                    'codigo': denuncia.codigo,  # Primary key del modelo
                    'fecha': denuncia.fecha.isoformat() if denuncia.fecha else '',
                    'categoria_id': denuncia.item.categoria.id,
                    'categoria_nombre': denuncia.item.categoria.nombre,
                    'item_enunciado': denuncia.item.enunciado,
                    'usuario_nombre': denuncia.usuario.nombre_completo,
                    'usuario_anonimo': denuncia.usuario.anonimo,
                    'estado_actual': denuncia.estado_actual,
                    'num_archivos': denuncia.num_archivos,
                    'num_mensajes_leidos': denuncia.num_mensajes_leidos,
                    'num_mensajes_no_leidos': denuncia.num_mensajes_no_leidos,
                    'num_mensajes_total': denuncia.num_mensajes_total,
                    'relacion_empresa': denuncia.relacion_empresa.rol,
                    'tiempo': denuncia.tiempo.intervalo,
                })
            
            # Respuesta
            response_data = {
                'draw': dt_data.get('draw', 1),
                'recordsTotal': records_filtered,
                'recordsFiltered': records_filtered,
                'data': data
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"Error en SimpleDenunciaDataTableAPIView: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'draw': request.data.get('draw', 1),
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': []
            }, status=500)
    
    def _parse_datatable_request(self, request):
        """Parsear request de DataTables"""
        try:
            # Si viene como JSON
            if request.content_type == 'application/json':
                return json.loads(request.body)
            # Si viene como form data
            else:
                return request.POST.dict()
        except:
            return {}
    
    def _apply_search(self, queryset, search_value):
        """Aplicar búsqueda global"""
        return queryset.filter(
            Q(codigo__icontains=search_value) |
            Q(usuario__nombre__icontains=search_value) |
            Q(usuario__apellidos__icontains=search_value) |
            Q(item__enunciado__icontains=search_value) |
            Q(item__categoria__nombre__icontains=search_value) |
            Q(descripcion__icontains=search_value) |
            Q(estado_actual__icontains=search_value)
        )
    
    def _apply_ordering(self, queryset, dt_data):
        """Aplicar ordenamiento"""
        # Mapeo de columnas a campos del modelo
        column_map = {
            0: 'codigo',
            1: 'fecha',
            2: 'item__categoria__nombre',
            3: 'item__enunciado',
            4: 'usuario__nombre',
            5: 'estado_actual'
        }
        
        # Obtener información de ordenamiento
        order_data = dt_data.get('order', [])
        if order_data and isinstance(order_data, list) and len(order_data) > 0:
            order = order_data[0]
            column_idx = int(order.get('column', 0))
            direction = order.get('dir', 'asc')
            
            if column_idx in column_map:
                field = column_map[column_idx]
                if direction == 'desc':
                    field = f'-{field}'
                return queryset.order_by(field)
        
        # Orden por defecto: fecha descendente
        return queryset.order_by('-fecha')
    


class DataTableActions(APIView):
    pass