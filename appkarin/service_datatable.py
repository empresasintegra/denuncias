# service_datatable_simple.py - API simplificada para DataTable de Denuncias
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from .models import Denuncia, Usuario, AdminDenuncias
import json


@method_decorator(csrf_exempt, name='dispatch')
class SimpleDenunciaDataTableAPIView(APIView):
    """
    API simplificada para DataTable de denuncias
    Maneja 4 tipos de usuarios:
    - Anónimo (DN-XXXXXX)
    - Identificado (XXXXX)
    - Admin por categoría
    - Super admin
    """
    
    def post(self, request, *args, **kwargs):
        try:
            # Parsear datos de DataTables
            dt_data = self._parse_datatable_request(request)
            
            # Obtener información del usuario
            user_info = dt_data.get('user_info', {})
            
            # Construir queryset base con optimizaciones
            queryset = Denuncia.objects.select_related(
                'usuario',
                'item',
                'item__categoria',
                'relacion_empresa',
                'tiempo'
            ).annotate(
                num_archivos=Count('archivo'),
                num_mensajes=Count('foro')
            )
            
            # Aplicar filtros según tipo de usuario
            queryset = self._apply_user_filters(queryset, user_info)
            
            # Aplicar búsqueda si existe
            search_value = dt_data.get('search', {}).get('value', '')
            if search_value:
                queryset = self._apply_search(queryset, search_value)
            
            # Contar registros
            records_filtered = queryset.count()
            
            # Aplicar ordenamiento
            queryset = self._apply_ordering(queryset, dt_data)
            
            # Paginar
            start = dt_data.get('start', 0)
            length = dt_data.get('length', 10)
            denuncias = queryset[start:start + length]
            
            # Serializar datos
            data = []
            for denuncia in denuncias:
                data.append({
                    'codigo': denuncia.codigo,
                    'fecha': denuncia.fecha.isoformat() if denuncia.fecha else '',
                    'categoria_nombre': denuncia.item.categoria.nombre,
                    'item_enunciado': denuncia.item.enunciado,
                    'usuario_nombre': denuncia.usuario.nombre_completo,
                    'usuario_anonimo': denuncia.usuario.anonimo,
                    'estado_actual': denuncia.estado_actual,
                    'num_archivos': denuncia.num_archivos,
                    'num_mensajes': denuncia.num_mensajes,
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
    
    def _apply_user_filters(self, queryset, user_info):
        """Aplicar filtros según tipo de usuario"""
        user_type = user_info.get('tipo', 'admin')
        codigo = user_info.get('codigo', '')
        
        if user_type == 'anonimo' and codigo:
            # Usuario anónimo: filtrar por ID de usuario
            queryset = queryset.filter(usuario__id=codigo)
            
        elif user_type == 'identificado' and codigo:
            # Usuario identificado: filtrar por ID de usuario
            queryset = queryset.filter(usuario__id=codigo)
            
        elif user_type == 'admin':
            # Verificar si es admin de categoría o superadmin
            categoria_id = user_info.get('categoria_id')
            is_superuser = user_info.get('is_superuser', False)
            
            if not is_superuser and categoria_id:
                # Admin de categoría: solo denuncias de su categoría
                queryset = queryset.filter(item__categoria_id=categoria_id)
            # Si es superuser, no se aplican filtros (ve todo)
        
        return queryset
    
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

