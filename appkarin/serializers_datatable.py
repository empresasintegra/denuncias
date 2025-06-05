# service_datatable.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
import json
import csv
from datetime import datetime

from .models import Denuncia, Usuario, Item, Categoria, RelacionEmpresa, Tiempo
from .serializers_datatable import (
    DenunciaDataTableSerializer,
    DataTableRequestSerializer,
    DataTableResponseSerializer,
    DenunciaFilterSerializer,
    DataTableConfigSerializer,
    DenunciaExportSerializer,
    DATATABLE_COLUMNS_CONFIG
)


@method_decorator(csrf_exempt, name='dispatch')
class DenunciaDataTableAPIView(APIView):
    """
    🎯 API principal para el DataTable dinámico de denuncias
    
    Soporta:
    - Server-side processing
    - Campos dinámicos
    - Filtros avanzados
    - Ordenamiento múltiple
    - Búsqueda global y por columna
    - Exportación a Excel/CSV
    """
    
    def post(self, request, *args, **kwargs):
        """Procesar petición del DataTable"""
        try:
            # 1️⃣ VALIDAR Y PARSEAR REQUEST
            dt_request = self._parse_datatable_request(request.data)
            
            # 2️⃣ CONSTRUIR QUERYSET OPTIMIZADO
            queryset = self._build_optimized_queryset()
            
            # 3️⃣ APLICAR FILTROS
            if dt_request.get('filters'):
                queryset = self._apply_filters(queryset, dt_request['filters'])
            
            # 4️⃣ APLICAR BÚSQUEDA GLOBAL
            search_value = dt_request.get('search', {}).get('value', '')
            if search_value:
                queryset = self._apply_global_search(queryset, search_value)
            
            # 5️⃣ APLICAR BÚSQUEDA POR COLUMNAS
            if dt_request.get('columns'):
                queryset = self._apply_column_search(queryset, dt_request['columns'])
            
            # 6️⃣ CONTAR REGISTROS
            records_total = Denuncia.objects.count()
            records_filtered = queryset.count()
            
            # 7️⃣ APLICAR ORDENAMIENTO
            if dt_request.get('order'):
                queryset = self._apply_ordering(queryset, dt_request['order'], dt_request.get('columns', []))
            else:
                queryset = queryset.order_by('-fecha')
            
            # 8️⃣ PAGINAR
            start = dt_request.get('start', 0)
            length = dt_request.get('length', 10)
            page_queryset = queryset[start:start + length]
            
            # 9️⃣ SERIALIZAR CON CAMPOS DINÁMICOS
            fields = dt_request.get('fields')
            serializer = DenunciaDataTableSerializer(
                page_queryset, 
                many=True,
                fields=fields,
                context={
                    'request': request,
                    'include_fields': fields or []
                }
            )
            
            # 🔟 PREPARAR RESPUESTA
            response_data = {
                'draw': dt_request.get('draw', 1),
                'recordsTotal': records_total,
                'recordsFiltered': records_filtered,
                'data': serializer.data
            }
            
            # Agregar agregaciones si se solicitan
            if request.data.get('include_aggregations'):
                response_data['aggregations'] = self._get_aggregations(queryset)
            
            return JsonResponse(response_data, safe=False)
            
        except Exception as e:
            print(f"❌ Error en DenunciaDataTableAPIView: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'error': str(e),
                'draw': request.data.get('draw', 1),
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': []
            }, status=500)
    
    def _parse_datatable_request(self, data):
        """Parsear y validar request de DataTables"""
        # DataTables puede enviar datos como form-data o JSON
        if isinstance(data, dict):
            return data
        
        # Parsear form-data de DataTables
        parsed = {
            'draw': int(data.get('draw', [1])[0]),
            'start': int(data.get('start', [0])[0]),
            'length': int(data.get('length', [10])[0]),
            'search': {
                'value': data.get('search[value]', [''])[0],
                'regex': data.get('search[regex]', ['false'])[0] == 'true'
            }
        }
        
        # Parsear columnas
        columns = []
        i = 0
        while f'columns[{i}][data]' in data:
            columns.append({
                'data': data.get(f'columns[{i}][data]', [''])[0],
                'name': data.get(f'columns[{i}][name]', [''])[0],
                'searchable': data.get(f'columns[{i}][searchable]', ['true'])[0] == 'true',
                'orderable': data.get(f'columns[{i}][orderable]', ['true'])[0] == 'true',
                'search': {
                    'value': data.get(f'columns[{i}][search][value]', [''])[0],
                    'regex': data.get(f'columns[{i}][search][regex]', ['false'])[0] == 'true'
                }
            })
            i += 1
        parsed['columns'] = columns
        
        # Parsear ordenamiento
        order = []
        i = 0
        while f'order[{i}][column]' in data:
            order.append({
                'column': int(data.get(f'order[{i}][column]', [0])[0]),
                'dir': data.get(f'order[{i}][dir]', ['asc'])[0]
            })
            i += 1
        parsed['order'] = order
        
        return parsed
    
    def _build_optimized_queryset(self):
        """Construir queryset con todas las optimizaciones necesarias"""
        return Denuncia.objects.select_related(
            'usuario',
            'item',
            'item__categoria',
            'relacion_empresa',
            'tiempo'
        ).prefetch_related(
            'archivo_set',
            'foro_set',
            'estadosdenuncia_set__estado'
        ).annotate(
            num_archivos=Count('archivo'),
            num_mensajes=Count('foro'),
            num_estados=Count('estadosdenuncia')
        )
    
    def _apply_filters(self, queryset, filters):
        """Aplicar filtros avanzados al queryset"""
        filter_serializer = DenunciaFilterSerializer(data=filters)
        
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data
            
            # Filtros de fecha
            if filters.get('fecha_desde'):
                queryset = queryset.filter(fecha__gte=filters['fecha_desde'])
            if filters.get('fecha_hasta'):
                queryset = queryset.filter(fecha__lte=filters['fecha_hasta'])
            
            # Filtros de relaciones
            if filters.get('usuario_id'):
                queryset = queryset.filter(usuario_id=filters['usuario_id'])
            
            if filters.get('usuario_tipo') != 'todos':
                if filters['usuario_tipo'] == 'anonimo':
                    queryset = queryset.filter(usuario__anonimo=True)
                else:
                    queryset = queryset.filter(usuario__anonimo=False)
            
            if filters.get('categoria_id'):
                queryset = queryset.filter(item__categoria_id=filters['categoria_id'])
            
            if filters.get('item_id'):
                queryset = queryset.filter(item_id=filters['item_id'])
            
            if filters.get('relacion_empresa_id'):
                queryset = queryset.filter(relacion_empresa_id=filters['relacion_empresa_id'])
            
            if filters.get('tiempo_id'):
                queryset = queryset.filter(tiempo_id=filters['tiempo_id'])
            
            # Filtros de estado
            if filters.get('estado_actual'):
                queryset = queryset.filter(estado_actual__in=filters['estado_actual'])
            
            # Filtros booleanos
            if filters.get('tiene_archivos') is not None:
                if filters['tiene_archivos']:
                    queryset = queryset.filter(num_archivos__gt=0)
                else:
                    queryset = queryset.filter(num_archivos=0)
            
            if filters.get('tiene_mensajes_foro') is not None:
                if filters['tiene_mensajes_foro']:
                    queryset = queryset.filter(num_mensajes__gt=0)
                else:
                    queryset = queryset.filter(num_mensajes=0)
            
            if filters.get('tiene_descripcion_relacion') is not None:
                if filters['tiene_descripcion_relacion']:
                    queryset = queryset.exclude(descripcion_relacion__isnull=True).exclude(descripcion_relacion='')
                else:
                    queryset = queryset.filter(Q(descripcion_relacion__isnull=True) | Q(descripcion_relacion=''))
            
            # Filtros de texto
            if filters.get('descripcion_contiene'):
                queryset = queryset.filter(descripcion__icontains=filters['descripcion_contiene'])
            
            if filters.get('codigo_contiene'):
                queryset = queryset.filter(codigo__icontains=filters['codigo_contiene'])
        
        return queryset
    
    def _apply_global_search(self, queryset, search_value):
        """Aplicar búsqueda global en múltiples campos"""
        search_fields = [
            'codigo',
            'usuario__id',
            'usuario__nombre',
            'usuario__apellidos',
            'usuario__rut',
            'usuario__correo',
            'item__enunciado',
            'item__categoria__nombre',
            'relacion_empresa__rol',
            'tiempo__intervalo',
            'descripcion',
            'estado_actual'
        ]
        
        # Construir Q objects para búsqueda
        q_objects = Q()
        for field in search_fields:
            q_objects |= Q(**{f'{field}__icontains': search_value})
        
        return queryset.filter(q_objects)
    
    def _apply_column_search(self, queryset, columns):
        """Aplicar búsqueda por columnas específicas"""
        column_field_mapping = {
            'codigo': 'codigo',
            'usuario_nombre': 'usuario__nombre',
            'usuario_id': 'usuario__id',
            'usuario_rut': 'usuario__rut',
            'categoria_nombre': 'item__categoria__nombre',
            'item_enunciado': 'item__enunciado',
            'relacion_empresa_rol': 'relacion_empresa__rol',
            'tiempo_intervalo': 'tiempo__intervalo',
            'estado_actual': 'estado_actual',
            'descripcion': 'descripcion'
        }
        
        for column in columns:
            if column.get('searchable') and column['search'].get('value'):
                field_name = column.get('data')
                search_value = column['search']['value']
                
                if field_name in column_field_mapping:
                    db_field = column_field_mapping[field_name]
                    queryset = queryset.filter(**{f'{db_field}__icontains': search_value})
        
        return queryset
    
    def _apply_ordering(self, queryset, order_list, columns):
        """Aplicar ordenamiento múltiple"""
        order_fields = []
        
        column_field_mapping = {
            'codigo': 'codigo',
            'fecha': 'fecha',
            'fecha_actualizacion': 'fecha_actualizacion',
            'usuario_nombre': 'usuario__nombre',
            'usuario_id': 'usuario__id',
            'categoria_nombre': 'item__categoria__nombre',
            'item_enunciado': 'item__enunciado',
            'relacion_empresa_rol': 'relacion_empresa__rol',
            'tiempo_intervalo': 'tiempo__intervalo',
            'estado_actual': 'estado_actual',
            'total_archivos': 'num_archivos',
            'total_mensajes_foro': 'num_mensajes'
        }
        
        for order in order_list:
            column_idx = order['column']
            direction = order['dir']
            
            if column_idx < len(columns):
                field_name = columns[column_idx].get('data')
                
                if field_name in column_field_mapping:
                    db_field = column_field_mapping[field_name]
                    if direction == 'desc':
                        db_field = f'-{db_field}'
                    order_fields.append(db_field)
        
        if order_fields:
            return queryset.order_by(*order_fields)
        
        return queryset
    
    def _get_aggregations(self, queryset):
        """Obtener agregaciones y estadísticas"""
        from django.db.models import Count, Avg
        from django.utils import timezone
        
        aggregations = {
            'total_denuncias': queryset.count(),
            'por_estado': dict(
                queryset.values('estado_actual').annotate(
                    count=Count('codigo')
                ).values_list('estado_actual', 'count')
            ),
            'por_categoria': dict(
                queryset.values('item__categoria__nombre').annotate(
                    count=Count('codigo')
                ).values_list('item__categoria__nombre', 'count')
            ),
            'usuarios_anonimos': queryset.filter(usuario__anonimo=True).count(),
            'usuarios_identificados': queryset.filter(usuario__anonimo=False).count(),
            'con_archivos': queryset.filter(num_archivos__gt=0).count(),
            'con_mensajes': queryset.filter(num_mensajes__gt=0).count(),
            'promedio_descripcion': int(
                queryset.aggregate(
                    avg_length=Avg('descripcion__length')
                )['avg_length'] or 0
            )
        }
        
        return aggregations


@method_decorator(csrf_exempt, name='dispatch')
class DenunciaDataTableConfigAPIView(APIView):
    """
    🎯 API para obtener configuración del DataTable
    """
    
    def get(self, request, *args, **kwargs):
        """Obtener configuración de columnas"""
        config_type = request.GET.get('type', 'basic')
        
        if config_type not in DATATABLE_COLUMNS_CONFIG:
            config_type = 'basic'
        
        columns = DATATABLE_COLUMNS_CONFIG[config_type]
        
        # Agregar configuración adicional
        for i, col in enumerate(columns):
            col['data'] = col['field']
            col['orderable'] = col.get('orderable', True)
            col['searchable'] = col.get('searchable', True)
            col['visible'] = col.get('visible', True)
        
        config = {
            'columns': columns,
            'default_order': [[0, 'desc']],
            'page_length': 25,
            'length_menu': [10, 25, 50, 100],
            'responsive': True,
            'server_side': True
        }
        
        serializer = DataTableConfigSerializer(config)
        
        return JsonResponse({
            'success': True,
            'config': serializer.data,
            'available_types': list(DATATABLE_COLUMNS_CONFIG.keys())
        })


@method_decorator(csrf_exempt, name='dispatch')
class DenunciaExportAPIView(APIView):
    """
    🎯 API para exportar denuncias a Excel o CSV
    """
    
    def post(self, request, *args, **kwargs):
        """Exportar denuncias con filtros aplicados"""
        try:
            export_format = request.data.get('format', 'excel').lower()
            filters = request.data.get('filters', {})
            
            # Construir queryset con filtros
            queryset = Denuncia.objects.select_related(
                'usuario', 'item', 'item__categoria', 
                'relacion_empresa', 'tiempo'
            )
            
            # Aplicar filtros si existen
            if filters:
                view = DenunciaDataTableAPIView()
                queryset = view._apply_filters(queryset, filters)
            
            # Serializar datos
            serializer = DenunciaExportSerializer(queryset, many=True)
            data = serializer.data
            
            if export_format == 'csv':
                return self._export_csv(data)
            else:
                return self._export_excel(data)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _export_pdf(self, data):
        """Exportar a CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="denuncias_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        if data:
            writer = csv.DictWriter(response, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return response
    


# =================================================================
# VISTAS ADICIONALES ÚTILES
# =================================================================

@method_decorator(csrf_exempt, name='dispatch')
class DenunciaDataTableStatsAPIView(APIView):
    """
    🎯 API para obtener estadísticas rápidas
    """
    
    def get(self, request, *args, **kwargs):
        """Obtener estadísticas generales"""
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        stats = {
            'totales': {
                'total_denuncias': Denuncia.objects.count(),
                'pendientes': Denuncia.objects.filter(estado_actual='PENDIENTE').count(),
                'en_revision': Denuncia.objects.filter(estado_actual='EN_REVISION').count(),
                'resueltas': Denuncia.objects.filter(estado_actual='RESUELTO').count(),
            },
            'ultimos_30_dias': {
                'nuevas': Denuncia.objects.filter(fecha__gte=last_30_days).count(),
                'resueltas': Denuncia.objects.filter(
                    estado_actual='RESUELTO',
                    fecha_actualizacion__gte=last_30_days
                ).count(),
            },
            'por_categoria': dict(
                Denuncia.objects.values('item__categoria__nombre').annotate(
                    total=Count('codigo')
                ).values_list('item__categoria__nombre', 'total')
            ),
            'usuarios': {
                'anonimos': Denuncia.objects.filter(usuario__anonimo=True).count(),
                'identificados': Denuncia.objects.filter(usuario__anonimo=False).count(),
            }
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'generated_at': timezone.now().isoformat()
        })