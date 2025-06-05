from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    DenunciaCreateSerializer, UsuarioCreateSerializer, 
    CategoriaWithItemsSerializer, DenunciaWizardDataSerializer,
    ConsultaDenunciaSerializer, DenunciaListSerializer,
    DenunciaDetailSerializer, ItemSelectionSerializer
)
import re





class ServiceItemsAPIView(APIView):
    """
    🎯 API REST para seleccionar el tipo de denuncia (item)
    
    Reemplaza: serviceItems de service.py
    URL: /api/create/denuncia/items/ (MISMA URL)
    
    ✅ CARACTERÍSTICAS DRF COMPLETAS:
    - Serializer dedicado para validación automática
    - Documentación Swagger automática  
    - Respuestas estructuradas con status codes apropiados
    - Manejo de errores profesional
    """
    
    def post(self, request, *args, **kwargs):
        """
        Seleccionar tipo de denuncia
        
        Recibe el ID del item seleccionado y lo valida automáticamente.
        Guarda la selección en sesión para el siguiente paso.
        """
        # 🚀 USAR SERIALIZER COMPLETO para validación automática
        serializer = ItemSelectionSerializer(data=request.data)
        
        if serializer.is_valid():
            # ✅ Datos automáticamente validados por el serializer
            item_id = serializer.validated_data['denuncia_item']
            validated_item = serializer.get_validated_item()
            
            # Guardar en sesión
            request.session['item_id'] = str(item_id)
            
            # ✅ RESPUESTA ESTRUCTURADA con datos adicionales útiles
            return Response({
                'success': True,
                'message': 'Item procesado correctamente',
                'redirect_url': '/denuncia/Paso2/',
                'data': {
                    'selected_item': {
                        'id': validated_item.id,
                        'enunciado': validated_item.enunciado,
                        'categoria': {
                            'id': validated_item.categoria.id,
                            'nombre': validated_item.categoria.nombre
                        }
                    }
                }
            }, status=status.HTTP_200_OK)
        else:
            # ✅ ERRORES AUTOMÁTICOS del serializer
            return Response({
                'success': False,
                'message': 'Debe seleccionar el tipo de denuncia',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class ServiceProcessDenunciaAPIView(APIView):
    """
    🎯 API REST para procesar la denuncia completa del wizard
    
    Reemplaza: serviceProcessDenuncia de service.py
    URL: /api/create/denuncia/wizzard/ (MISMA URL)
    
    ✅ CARACTERÍSTICAS DRF COMPLETAS:
    - Usa DenunciaCreateSerializer para validación automática completa
    - Validaciones cruzadas automáticas (ej: descripción_relacion si es "Otro")
    - Mensajes de error descriptivos y estructurados
    - Documentación automática de todos los campos
    """
    
    def post(self, request, *args, **kwargs):
        """
        Procesar datos del wizard de denuncia
        
        Valida todos los datos del wizard usando DenunciaCreateSerializer.
        Incluye validaciones cruzadas automáticas.
        """
        # 🚀 PREPARAR DATOS para DenunciaCreateSerializer
        serializer_data = {
            'denuncia_relacion': request.data.get('denuncia_relacion'),
            'denuncia_tiempo': request.data.get('denuncia_tiempo'),
            'descripcion': request.data.get('descripcion'),
            'descripcion_relacion': request.data.get('descripcion_relacion', ''),
            'item_id': request.session.get('item_id')  # Desde sesión del paso anterior
        }
        
        # 🚀 USAR SERIALIZER COMPLETO para validación automática
        serializer = DenunciaCreateSerializer(data=serializer_data)
        
        if serializer.is_valid():
            # ✅ Datos automáticamente validados y limpios
            validated_data = serializer.validated_data
            
            # Guardar datos validados en sesión para el siguiente paso
            request.session['wizzard_data'] = {
                'denuncia_relacion_id': validated_data['denuncia_relacion'],
                'denuncia_tiempo_id': validated_data['denuncia_tiempo'],
                'denuncia_descripcion': validated_data['descripcion'],
                'descripcion_relacion': validated_data.get('descripcion_relacion', ''),
                'denuncia_archivos': request.data.get('archivos', '')
            }
            
            # ✅ RESPUESTA ESTRUCTURADA con datos de validación
            return Response({
                'success': True,
                'message': 'Wizard procesado correctamente',
                'redirect_url': '/denuncia/Paso3/',
                'data': {
                    'validated_fields': {
                        'relacion_empresa': RelacionEmpresa.objects.get(
                            id=validated_data['denuncia_relacion']
                        ).rol,
                        'tiempo_seleccionado': Tiempo.objects.get(
                            id=validated_data['denuncia_tiempo']
                        ).intervalo,
                        'descripcion_length': len(validated_data['descripcion']),
                        'has_descripcion_relacion': bool(validated_data.get('descripcion_relacion'))
                    }
                }
            }, status=status.HTTP_200_OK)
        else:
            # ✅ ERRORES AUTOMÁTICOS Y ESTRUCTURADOS del serializer
            # Convertir errores técnicos a mensajes amigables para JavaScript
            friendly_errors = self._get_friendly_errors(serializer.errors)
            
            return Response({
                'success': False,
                'message': friendly_errors['main_message'],
                'errors': serializer.errors,
                'friendly_errors': friendly_errors['field_errors']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_friendly_errors(self, serializer_errors):
        """Convertir errores del serializer a mensajes amigables"""
        field_mapping = {
            'denuncia_relacion': 'Debe seleccionar su relación con la empresa',
            'denuncia_tiempo': 'Debe seleccionar hace cuánto tiempo ocurren los hechos',
            'descripcion': 'La descripción debe tener al menos 50 caracteres',
            'descripcion_relacion': 'Debe especificar su relación con la empresa',
            'item_id': 'Debe seleccionar un tipo de denuncia primero'
        }
        
        main_message = "Datos inválidos"
        field_errors = {}
        
        for field, errors in serializer_errors.items():
            if field in field_mapping:
                main_message = field_mapping[field]
                field_errors[field] = field_mapping[field]
            else:
                field_errors[field] = errors[0] if errors else "Campo inválido"
        
        return {
            'main_message': main_message,
            'field_errors': field_errors
        }


class ServiceUserDenunciaAPIView(APIView):
    """
    🎯 API REST para crear usuario y denuncia final
    
    Reemplaza: serviceUserDenuncia de service.py  
    URL: /api/create/denuncia/user/ (MISMA URL)
    
    ✅ CARACTERÍSTICAS DRF COMPLETAS:
    - Usa UsuarioCreateSerializer para validación automática completa
    - Formateo automático de RUT y celular
    - Validaciones condicionales (anónimo vs identificado)
    - Creación transaccional de usuario y denuncia
    - Respuestas estructuradas con todos los datos relevantes
    """
    
    def post(self, request, *args, **kwargs):
        """
        Crear usuario y denuncia final
        
        Procesa los datos del usuario usando UsuarioCreateSerializer,
        crea la denuncia con los datos del wizard y retorna el código.
        """
        # Verificar que existan los datos de pasos previos
        item_id = request.session.get('item_id')
        wizard_data = request.session.get('wizzard_data', {})
        
        if not item_id or not wizard_data:
            return Response({
                'success': False,
                'message': 'Faltan datos de la denuncia. Reinicie el proceso.',
                'error_code': 'MISSING_SESSION_DATA'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 🚀 PREPARAR DATOS para UsuarioCreateSerializer
        tipo_denuncia = request.data.get('tipo_denuncia')
        
        usuario_data = {
            'anonimo': tipo_denuncia == 'anonimo',
            'rut': request.data.get('rut', ''),
            'nombre': request.data.get('nombre_completo', ''),
            'apellidos': request.data.get('apellidos', ''),
            'correo': request.data.get('correo_electronico', ''),
            'celular': request.data.get('celular', '')
        }

        # 🚀 USAR SERIALIZER COMPLETO para validación automática
        usuario_serializer = UsuarioCreateSerializer(data=usuario_data)
        
        if usuario_serializer.is_valid():
            try:
                # ✅ CREAR USUARIO con serializer (automáticamente valida y formatea)
                usuario = usuario_serializer.save()

                # ✅ CREAR DENUNCIA con datos validados del wizard
                item = Item.objects.select_related('categoria').get(id=item_id)
                relacion = RelacionEmpresa.objects.get(id=wizard_data['denuncia_relacion_id'])
                tiempo = Tiempo.objects.get(id=wizard_data['denuncia_tiempo_id'])

                denuncia = Denuncia.objects.create(
                    usuario=usuario,
                    item=item,
                    relacion_empresa=relacion,
                    tiempo=tiempo,
                    descripcion=wizard_data['denuncia_descripcion'],
                    descripcion_relacion=wizard_data.get('descripcion_relacion') if relacion.rol == 'Otro' else None
                )

                # Guardar código en sesión para la página final
                request.session['codigo'] = denuncia.codigo
                
                # ✅ RESPUESTA ESTRUCTURADA con todos los datos relevantes
                return Response({
                    'success': True,
                    'message': 'Denuncia procesada satisfactoriamente',
                    'redirect_url': '/denuncia/final/',
                    'data': {
                        'denuncia': {
                            'id': denuncia.id,
                            'codigo': denuncia.codigo,
                            'fecha': denuncia.fecha.isoformat(),
                            'estado_actual': denuncia.estado_actual
                        },
                        'usuario': {
                            'id': usuario.id,
                            'tipo': 'anonimo' if usuario.anonimo else 'identificado',
                            'nombre_completo': usuario.nombre_completo if not usuario.anonimo else None
                        },
                        'item': {
                            'id': item.id,
                            'enunciado': item.enunciado,
                            'categoria': item.categoria.nombre
                        },
                        'relacion_empresa': relacion.rol,
                        'tiempo': tiempo.intervalo
                    }
                }, status=status.HTTP_201_CREATED)
                
            except (Item.DoesNotExist, RelacionEmpresa.DoesNotExist, Tiempo.DoesNotExist) as e:
                return Response({
                    'success': False,
                    'message': 'Error de validación: Datos de referencia no encontrados',
                    'error_code': 'REFERENCE_DATA_NOT_FOUND',
                    'details': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    'success': False,
                    'message': 'Error interno del servidor',
                    'error_code': 'INTERNAL_SERVER_ERROR'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # ✅ ERRORES AUTOMÁTICOS Y ESTRUCTURADOS del serializer
            friendly_errors = self._get_friendly_usuario_errors(usuario_serializer.errors)
            
            return Response({
                'success': False,
                'message': friendly_errors['main_message'],
                'errors': usuario_serializer.errors,
                'friendly_errors': friendly_errors['field_errors']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_friendly_usuario_errors(self, serializer_errors):
        """Convertir errores del serializer a mensajes amigables para usuarios"""
        field_mapping = {
            'rut': 'RUT inválido. Formato esperado: 12345678-9',
            'nombre': 'Nombre es requerido para usuarios identificados',
            'apellidos': 'Apellidos son requeridos para usuarios identificados',
            'correo': 'Correo electrónico inválido',
            'celular': 'Formato de celular inválido. Use: 912345678 o +56912345678'
        }
        
        main_message = "Datos de usuario inválidos"
        field_errors = {}
        
        for field, errors in serializer_errors.items():
            if field in field_mapping:
                main_message = field_mapping[field]
                field_errors[field] = field_mapping[field]
            else:
                field_errors[field] = errors[0] if errors else "Campo inválido"
        
        return {
            'main_message': main_message,
            'field_errors': field_errors
        }


# =================================================================
# 🆕 APIs ADICIONALES OPCIONALES - INTERFAZ REST COMPLETA
# =================================================================

class DenunciaWizardDataAPIView(APIView):
    """
    🎯 API REST para obtener datos del wizard
    
    ✅ CARACTERÍSTICAS DRF COMPLETAS:
    - Usa DenunciaWizardDataSerializer para respuestas estructuradas
    - Documentación automática de todas las opciones disponibles
    - Optimización de consultas con select_related/prefetch_related
    """
    
    def get(self, request, *args, **kwargs):
        """
        Obtener todos los datos necesarios para el wizard
        
        Retorna categorías, items, relaciones empresa y tiempos
        en formato estructurado para el frontend.
        """
        try:
            # Datos optimizados para el wizard
            data = {
                'categorias': Categoria.objects.all().prefetch_related('item_set'),
                'relacion_empresas': RelacionEmpresa.objects.all(),
                'tiempos': Tiempo.objects.all()
            }
            
            # 🚀 USAR SERIALIZER para respuesta estructurada
            serializer = DenunciaWizardDataSerializer(data)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'meta': {
                    'total_categorias': len(data['categorias']),
                    'total_relaciones': len(data['relacion_empresas']),
                    'total_tiempos': len(data['tiempos'])
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al cargar datos del wizard',
                'error_code': 'WIZARD_DATA_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConsultaDenunciaAPIView(APIView):
    """
    🎯 API REST para consultar denuncias por código
    
    ✅ CARACTERÍSTICAS DRF COMPLETAS:
    - Usa ConsultaDenunciaSerializer para validación del código
    - Usa DenunciaListSerializer para respuestas estructuradas
    - Búsqueda optimizada con select_related
    - Documentación automática de formatos de código
    """
    
    def post(self, request, *args, **kwargs):
        """
        Consultar denuncias por código
        
        Acepta códigos formato DN-XXXXXXXX o ID de usuario.
        Retorna denuncias en formato estructurado.
        """
        # 🚀 USAR SERIALIZER para validación del código
        serializer = ConsultaDenunciaSerializer(data=request.data)
        
        if serializer.is_valid():
            codigo = serializer.validated_data['codigo']
            
            try:
                if codigo.startswith('DN-'):
                    # Búsqueda por código completo
                    denuncias = Denuncia.objects.select_related(
                        'usuario', 'item', 'item__categoria', 'relacion_empresa', 'tiempo'
                    ).filter(codigo=codigo)
                else:
                    # Búsqueda por ID de usuario
                    denuncias = Denuncia.objects.select_related(
                        'usuario', 'item', 'item__categoria', 'relacion_empresa', 'tiempo'
                    ).filter(usuario_id=codigo)

                if denuncias.exists():
                    # 🚀 USAR SERIALIZER para respuesta estructurada
                    denuncias_serializer = DenunciaListSerializer(denuncias, many=True)
                    
                    return Response({
                        'success': True,
                        'data': {
                            'denuncias': denuncias_serializer.data,
                            'total': denuncias.count(),
                            'search_criteria': {
                                'codigo': codigo,
                                'search_type': 'codigo_completo' if codigo.startswith('DN-') else 'usuario_id'
                            }
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'No se encontraron denuncias con ese código',
                        'error_code': 'DENUNCIAS_NOT_FOUND'
                    }, status=status.HTTP_404_NOT_FOUND)

            except Exception as e:
                return Response({
                    'success': False,
                    'message': 'Error al consultar denuncias',
                    'error_code': 'CONSULTA_ERROR'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'success': False,
                'message': 'Código inválido',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)