from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    DenunciaCreateSerializer, UsuarioCreateSerializer, 
    CategoriaWithItemsSerializer, DenunciaWizardDataSerializer,
    ConsultaDenunciaSerializer, DenunciaListSerializer,
    ItemSelectionSerializer,AdminSerializer
)
import re
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import time





@method_decorator(csrf_exempt, name='dispatch')
class AutocompleteUserDataAPIView(APIView):
    """
    🎯 API para autocompletar datos del usuario basado en RUT
    
    Si el RUT existe, devuelve los datos para autocompletado
    """
    
    def post(self, request, *args, **kwargs):
        """Obtener datos del usuario para autocompletado"""
        try:
            rut = request.data.get('rut', '').strip()
            
            if not rut:
                return JsonResponse({
                    'success': False,
                    'message': 'RUT requerido'
                }, status=400)
            
            # Buscar usuario
            usuario = Usuario.objects.filter(rut__iexact=rut).first()
            
            if usuario and not usuario.anonimo:
                # Solo autocompletar si no es anónimo
                return JsonResponse({
                    'success': True,
                    'autocomplete_data': {
                        'nombre_completo': usuario.nombre,
                        'apellidos': usuario.apellidos,
                        'correo_electronico': usuario.correo,
                        'celular': usuario.celular.replace('+569', '') if usuario.celular else ''
                    },
                    'message': 'Datos encontrados y autocompletados'
                }, json_dumps_params={'ensure_ascii': False})
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontraron datos para autocompletar'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error al obtener datos'
            }, status=500)




@method_decorator(csrf_exempt, name='dispatch')
class ValidateRutAPIView(APIView):
    """
    🎯 API REST para validar RUT en tiempo real
    
    Busca si un RUT ya existe en la base de datos de usuarios
    y valida su formato.
    """
    
    def post(self, request, *args, **kwargs):
        """
        Validar RUT y verificar si existe en la base de datos
        
        Entrada:
        - rut: String con el RUT a validar (formato: 12345678-9)
        
        Salida:
        - valid: Boolean - Si el RUT tiene formato válido
        - exists: Boolean - Si el RUT ya existe en la DB
        - message: String - Mensaje descriptivo
        - user_info: Object - Información del usuario si existe (opcional)
        """
        try:
            # ✅ SIMULAR DELAY DEL SERVIDOR (2 segundos máximo)
            time.sleep(0.5)  # Simular tiempo de respuesta del servidor
            
            # ✅ OBTENER Y LIMPIAR RUT
            rut_input = request.data.get('rut', '').strip()
            
            if not rut_input:
                return JsonResponse({
                    'success': False,
                    'valid': False,
                    'exists': False,
                    'message': 'RUT requerido'
                }, status=400, json_dumps_params={'ensure_ascii': False})
            
            print(f"🔍 Validando RUT: {rut_input}")
            
            # ✅ VALIDAR FORMATO DE RUT
            try:
                validate_rut(rut_input)
                rut_is_valid = True
                print("✅ RUT con formato válido")
            except Exception as e:
                print(f"❌ RUT con formato inválido: {str(e)}")
                return JsonResponse({
                    'success': True,  # Success porque la operación se completó
                    'valid': False,
                    'exists': False,
                    'message': f'RUT inválido: {str(e)}',
                    'error_type': 'format_error'
                }, status=200, json_dumps_params={'ensure_ascii': False})
            
            # ✅ BUSCAR RUT EN BASE DE DATOS
            try:
                # Limpiar RUT para búsqueda (remover puntos y guión)
                rut_limpio = rut_input.replace('.', '').replace('-', '').upper()
                
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
                    
                    return JsonResponse({
                        'success': True,
                        'valid': True,
                        'exists': True,
                        'message': 'Este RUT ya está registrado en nuestro sistema',
                        'user_info': user_info,
                        'suggestion': 'Sus datos pueden ser autocompletados'
                    }, status=200, json_dumps_params={'ensure_ascii': False})
                    
                else:
                    print("✅ RUT válido y disponible")
                    
                    # ✅ RUT VÁLIDO Y NO EXISTE
                    return JsonResponse({
                        'success': True,
                        'valid': True,
                        'exists': False,
                        'message': 'RUT válido y disponible',
                        'suggestion': 'Puede continuar con el registro'
                    }, status=200, json_dumps_params={'ensure_ascii': False})
                    
            except Exception as e:
                print(f"❌ Error al buscar en base de datos: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'valid': True,  # Formato OK, pero error en DB
                    'exists': False,
                    'message': 'Error al verificar RUT en la base de datos',
                    'error_type': 'database_error'
                }, status=500, json_dumps_params={'ensure_ascii': False})
                
        except Exception as e:
            print(f"❌ Error general en validación de RUT: {str(e)}")
            return JsonResponse({
                'success': False,
                'valid': False,
                'exists': False,
                'message': 'Error interno del servidor',
                'error_type': 'server_error'
            }, status=500, json_dumps_params={'ensure_ascii': False})


class ServiceAdminResetPassword(APIView):

    """
    🎯 API REST para generar el reset password
    """

    def post(self, request, *args, **kwargs):
        try:
            print(f"📥 Datos recibidos en items: {request.data}")
            print(f"📥 Content type: {request.content_type}")
            
            # 🚀 USAR SERIALIZER COMPLETO para validación automática
            serializer = AdminSerializer(data=request.data)
            
            if serializer.is_valid():
                # ✅ Datos automáticamente validados por el serializer
                item_id = serializer.validated_data['denuncia_item']
                validated_item = serializer.get_validated_item()
                
                # ✅ RESPUESTA JSON CORRECTA con encoding UTF-8
                response_data = {
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
                }
                
                # ✅ RETORNAR JsonResponse con encoding correcto
                return JsonResponse(
                    response_data, 
                    status=200,
                    json_dumps_params={'ensure_ascii': False}  # ✅ Para caracteres especiales
                )
            else:
                print(f"❌ Errores de validación: {serializer.errors}")
                # ✅ ERRORES AUTOMÁTICOS del serializer
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar el tipo de denuncia',
                    'errors': serializer.errors
                }, status=400, json_dumps_params={'ensure_ascii': False})
                
        except Exception as e:
            print(f"❌ Error en ServiceItemsAPIView: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor',
                'error': str(e)
            }, status=500, json_dumps_params={'ensure_ascii': False})




class ServiceLoginAdminAPIView(APIView):

    """
    🎯 API REST para generar el login de Admin
    """

    def post(self, request, *args, **kwargs):
        try:
            print(f"📥 Datos recibidos en items: {request.data}")
            print(f"📥 Content type: {request.content_type}")
            
            # 🚀 USAR SERIALIZER COMPLETO para validación automática
            serializer = ItemSelectionSerializer(data=request.data)
            
            if serializer.is_valid():
                # ✅ Datos automáticamente validados por el serializer
                item_id = serializer.validated_data['denuncia_item']
                validated_item = serializer.get_validated_item()
                
                # ⭐ GUARDAR EN SESIÓN CORRECTAMENTE
                request.session['item_id'] = str(item_id)
                request.session.save()  # ✅ Forzar guardado inmediato
                
                print(f"✅ Item guardado en sesión: {item_id}")
                print(f"🔍 Sesión actual: {dict(request.session)}")
                
                # ✅ RESPUESTA JSON CORRECTA con encoding UTF-8
                response_data = {
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
                }
                
                # ✅ RETORNAR JsonResponse con encoding correcto
                return JsonResponse(
                    response_data, 
                    status=200,
                    json_dumps_params={'ensure_ascii': False}  # ✅ Para caracteres especiales
                )
            else:
                print(f"❌ Errores de validación: {serializer.errors}")
                # ✅ ERRORES AUTOMÁTICOS del serializer
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar el tipo de denuncia',
                    'errors': serializer.errors
                }, status=400, json_dumps_params={'ensure_ascii': False})
                
        except Exception as e:
            print(f"❌ Error en ServiceItemsAPIView: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor',
                'error': str(e)
            }, status=500, json_dumps_params={'ensure_ascii': False})






class ServiceItemsAPIView(APIView):
    """
    🎯 API REST para seleccionar el tipo de denuncia (item)
    """
    
    def post(self, request, *args, **kwargs):
        """Seleccionar tipo de denuncia"""
        try:
            print(f"📥 Datos recibidos en items: {request.data}")
            print(f"📥 Content type: {request.content_type}")
            
            # 🚀 USAR SERIALIZER COMPLETO para validación automática
            serializer = ItemSelectionSerializer(data=request.data)
            
            if serializer.is_valid():
                # ✅ Datos automáticamente validados por el serializer
                item_id = serializer.validated_data['denuncia_item']
                validated_item = serializer.get_validated_item()
                
                # ⭐ GUARDAR EN SESIÓN CORRECTAMENTE
                request.session['item_id'] = str(item_id)
                request.session.save()  # ✅ Forzar guardado inmediato
                
                print(f"✅ Item guardado en sesión: {item_id}")
                print(f"🔍 Sesión actual: {dict(request.session)}")
                
                # ✅ RESPUESTA JSON CORRECTA con encoding UTF-8
                response_data = {
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
                }
                
                # ✅ RETORNAR JsonResponse con encoding correcto
                return JsonResponse(
                    response_data, 
                    status=200,
                    json_dumps_params={'ensure_ascii': False}  # ✅ Para caracteres especiales
                )
            else:
                print(f"❌ Errores de validación: {serializer.errors}")
                # ✅ ERRORES AUTOMÁTICOS del serializer
                return JsonResponse({
                    'success': False,
                    'message': 'Debe seleccionar el tipo de denuncia',
                    'errors': serializer.errors
                }, status=400, json_dumps_params={'ensure_ascii': False})
                
        except Exception as e:
            print(f"❌ Error en ServiceItemsAPIView: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor',
                'error': str(e)
            }, status=500, json_dumps_params={'ensure_ascii': False})


class ServiceProcessDenunciaAPIView(APIView):
    """
    🎯 API REST para procesar la denuncia completa del wizard
    """
    
    def post(self, request, *args, **kwargs):
        """Procesar datos del wizard de denuncia"""
        try:
            print(f"📥 Datos recibidos en wizard: {request.data}")
            print(f"📥 Content type: {request.content_type}")
            print(f"🔍 Sesión antes del wizard: {dict(request.session)}")

            # ✅ VERIFICAR DATOS DE SESIÓN PRIMERO
            item_id = request.session.get('item_id')
            if not item_id:
                print("❌ No se encontró item_id en sesión")
                return JsonResponse({
                    'success': False,
                    'message': 'Sesión expirada. Debe seleccionar el tipo de denuncia primero.',
                    'error_code': 'SESSION_EXPIRED'
                }, status=400, json_dumps_params={'ensure_ascii': False})

            # 🚀 PREPARAR DATOS para DenunciaCreateSerializer
            serializer_data = {
                'denuncia_relacion': request.data.get('denuncia_relacion'),
                'denuncia_tiempo': request.data.get('denuncia_tiempo'),
                'descripcion': request.data.get('descripcion'),
                'descripcion_relacion': request.data.get('descripcion_relacion', ''),
                'item_id': item_id  # Desde sesión del paso anterior
            }
            
            print(f"📊 Datos para serializer: {serializer_data}")
            
            # 🚀 USAR SERIALIZER COMPLETO para validación automática
            serializer = DenunciaCreateSerializer(data=serializer_data)
            print("✅ Serializer creado, validando...")
            
            if serializer.is_valid():
                print("✅ Serializer válido")
                # ✅ Datos automáticamente validados y limpios
                validated_data = serializer.validated_data
                
                # ⭐ GUARDAR DATOS VALIDADOS EN SESIÓN CORRECTAMENTE
                request.session['wizzard_data'] = {
                    'denuncia_relacion_id': validated_data['denuncia_relacion'],
                    'denuncia_tiempo_id': validated_data['denuncia_tiempo'],
                    'denuncia_descripcion': validated_data['descripcion'],
                    'descripcion_relacion': validated_data.get('descripcion_relacion', ''),
                    'denuncia_archivos': request.data.get('archivos', '')
                }
                request.session.save()  # ✅ Forzar guardado inmediato
                
                print(f"✅ Wizard data guardado: {request.session['wizzard_data']}")
                
                # ✅ RESPUESTA ESTRUCTURADA con datos de validación
                response_data = {
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
                }
                
                return JsonResponse(
                    response_data, 
                    status=200,
                    json_dumps_params={'ensure_ascii': False}
                )
            else:
                print(f"❌ Errores de validación del serializer: {serializer.errors}")
                # ✅ ERRORES AUTOMÁTICOS Y ESTRUCTURADOS del serializer
                friendly_errors = self._get_friendly_errors(serializer.errors)
                
                return JsonResponse({
                    'success': False,
                    'message': friendly_errors['main_message'],
                    'errors': serializer.errors,
                    'friendly_errors': friendly_errors['field_errors']
                }, status=400, json_dumps_params={'ensure_ascii': False})
                
        except Exception as e:
            print(f"❌ Error en ServiceProcessDenunciaAPIView: {str(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor',
                'error': str(e)
            }, status=500, json_dumps_params={'ensure_ascii': False})
    
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
    """
    
    def post(self, request, *args, **kwargs):
        """Crear usuario y denuncia final"""
        try:
            print(f"📥 Datos recibidos en usuario: {request.data}")
            print(f"📥 Content type: {request.content_type}")
            print(f"🔍 Sesión en usuario: {dict(request.session)}")
            
            # ✅ VERIFICAR DATOS DE SESIÓN CORRECTAMENTE
            item_id = request.session.get('item_id')
            wizard_data = request.session.get('wizzard_data', {})
            
            print(f"🔍 item_id: {item_id}")
            print(f"🔍 wizard_data: {wizard_data}")
            
            if not item_id or not wizard_data:
                print("❌ Faltan datos de sesión")
                return JsonResponse({
                    'success': False,
                    'message': 'Faltan datos de la denuncia. Reinicie el proceso.',
                    'error_code': 'MISSING_SESSION_DATA',
                    'debug': {
                        'item_id': item_id,
                        'wizard_data_exists': bool(wizard_data),
                        'session_keys': list(request.session.keys())
                    }
                }, status=400, json_dumps_params={'ensure_ascii': False})

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

            print(f"📊 Datos de usuario preparados: {usuario_data}")

            # 🚀 USAR SERIALIZER COMPLETO para validación automática
            usuario_serializer = UsuarioCreateSerializer(data=usuario_data)
            
            if usuario_serializer.is_valid():
                print("✅ Serializer de usuario válido")
                
                # ✅ CREAR USUARIO con serializer (automáticamente valida y formatea)
                usuario = usuario_serializer.save()
                print(f"✅ Usuario creado: {usuario.id}")

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
                    descripcion_relacion=wizard_data.get('descripcion_relacion') if relacion.rol.lower() == 'otro' else None
                )

                print(f"✅ Denuncia creada: {denuncia.codigo}")

                # ⭐ GUARDAR CÓDIGO EN SESIÓN
                request.session['codigo'] = denuncia.codigo
                request.session.save()
                
                # ✅ RESPUESTA ESTRUCTURADA con todos los datos relevantes
                response_data = {
                    'success': True,
                    'message': 'Denuncia procesada satisfactoriamente',
                    'redirect_url': '/denuncia/final/',
                    'data': {
                        'denuncia': {
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
                }
                
                return JsonResponse(
                    response_data, 
                    status=201,
                    json_dumps_params={'ensure_ascii': False}
                )
                
            else:
                print(f"❌ Errores de validación del usuario: {usuario_serializer.errors}")
                # ✅ ERRORES AUTOMÁTICOS Y ESTRUCTURADOS del serializer
                friendly_errors = self._get_friendly_usuario_errors(usuario_serializer.errors)
                
                return JsonResponse({
                    'success': False,
                    'message': friendly_errors['main_message'],
                    'errors': usuario_serializer.errors,
                    'friendly_errors': friendly_errors['field_errors']
                }, status=400, json_dumps_params={'ensure_ascii': False})
                
        except (Item.DoesNotExist, RelacionEmpresa.DoesNotExist, Tiempo.DoesNotExist) as e:
            print(f"❌ Error de datos de referencia: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error de validación: Datos de referencia no encontrados',
                'error_code': 'REFERENCE_DATA_NOT_FOUND',
                'details': str(e)
            }, status=400, json_dumps_params={'ensure_ascii': False})
        except Exception as e:
            print(f"❌ Error en ServiceUserDenunciaAPIView: {str(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor',
                'error_code': 'INTERNAL_SERVER_ERROR',
                'error': str(e)
            }, status=500, json_dumps_params={'ensure_ascii': False})
    
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
    """🎯 API REST para obtener datos del wizard"""
    
    def get(self, request, *args, **kwargs):
        """Obtener todos los datos necesarios para el wizard"""
        try:
            # Datos optimizados para el wizard
            data = {
                'categorias': Categoria.objects.all().prefetch_related('item_set'),
                'relacion_empresas': RelacionEmpresa.objects.all(),
                'tiempos': Tiempo.objects.all()
            }
            
            # 🚀 USAR SERIALIZER para respuesta estructurada
            serializer = DenunciaWizardDataSerializer(data)
            
            return JsonResponse({
                'success': True,
                'data': serializer.data,
                'meta': {
                    'total_categorias': len(data['categorias']),
                    'total_relaciones': len(data['relacion_empresas']),
                    'total_tiempos': len(data['tiempos'])
                }
            }, status=200, json_dumps_params={'ensure_ascii': False})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error al cargar datos del wizard',
                'error_code': 'WIZARD_DATA_ERROR'
            }, status=500, json_dumps_params={'ensure_ascii': False})


class ConsultaDenunciaAPIView(APIView):
    """🎯 API REST para consultar denuncias por código"""
    
    def post(self, request, *args, **kwargs):
        """Consultar denuncias por código"""
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
                    
                    return JsonResponse({
                        'success': True,
                        'data': {
                            'denuncias': denuncias_serializer.data,
                            'total': denuncias.count(),
                            'search_criteria': {
                                'codigo': codigo,
                                'search_type': 'codigo_completo' if codigo.startswith('DN-') else 'usuario_id'
                            }
                        }
                    }, status=200, json_dumps_params={'ensure_ascii': False})
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'No se encontraron denuncias con ese código',
                        'error_code': 'DENUNCIAS_NOT_FOUND'
                    }, status=404, json_dumps_params={'ensure_ascii': False})

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': 'Error al consultar denuncias',
                    'error_code': 'CONSULTA_ERROR'
                }, status=500, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse({
                'success': False,
                'message': 'Código inválido',
                'errors': serializer.errors
            }, status=400, json_dumps_params={'ensure_ascii': False})