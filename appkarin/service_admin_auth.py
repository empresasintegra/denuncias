# service_admin_auth.py - Servicio consolidado para autenticación de administradores
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import AdminDenuncias
import json


@method_decorator(csrf_exempt, name='dispatch')
class ServiceAdminDenunciaAuth(APIView):
    """
    Servicio consolidado para todas las operaciones de autenticación de administradores.
    Reemplaza: ServiceLoginAdminAPIView, ServiceLogoutAdminAPIView, ServiceCheckAuthAdminAPIView
    """
    
    def post(self, request, action=None):
        """
        POST /api/admin/auth/{action}/
        
        Acciones disponibles:
        - login: Autenticar administrador
        - logout: Cerrar sesión
        - check: Verificar estado de autenticación
        """
        try:
            if action == 'login':
                return self._handle_login(request)
            elif action == 'logout':
                return self._handle_logout(request)
            elif action == 'check':
                return self._handle_check_auth(request)
            else:
                return Response({
                    'success': False,
                    'message': f'Acción no válida: {action}'
                }, status=400)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error en autenticación: {str(e)}'
            }, status=500)
    
    def get(self, request, action=None):
        """
        GET /api/admin/auth/{action}/
        Solo para check auth
        """
        if action == 'check':
            return self._handle_check_auth(request)
        
        return Response({
            'success': False,
            'message': 'Método no permitido'
        }, status=405)
    
    def _handle_login(self, request):
        """
        Maneja el login de administradores
        Espera: { "username": "usuario", "password": "contraseña" }
        """
        try:

            username = request.data.get('username', '').strip()
            password = request.data.get('password', '')
            
            if not username or not password:
                return Response({
                    'success': False,
                    'message': 'Usuario y contraseña son requeridos'
                }, status=400)
            
            # Intentar autenticar con Django auth
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_active:
                # Usuario Django válido
                login(request, user)
                
                # Preparar datos de respuesta
                response_data = {
                    'success': True,
                    'message': 'Login exitoso',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_superuser': user.is_superuser,
                        'is_staff': user.is_staff,
                    },
                    'redirect_url': '/'
                }
                
                # Agregar información de categoría si existe
                if hasattr(user, 'rol_categoria') and user.rol_categoria:
                    response_data['user']['categoria'] = {
                        'id': user.rol_categoria.id,
                        'nombre': user.rol_categoria.nombre
                    }
                else:
                    response_data['user']['categoria'] = None
                
                # Guardar información en sesión
                request.session['admin_logged'] = True
                request.session['admin_id'] = user.id
                request.session['admin_username'] = user.username
                request.session['is_django_user'] = True
                
                return Response(response_data)
            
            # Si no es usuario Django, verificar en tabla AdminDenuncias (legacy)
            try:
                admin = AdminDenuncias.objects.get(
                    usuario=username,
                    estado=True  # Solo admins activos
                )
                
                # Verificar contraseña (deberías usar hashing en producción)
                if admin.password == password:  # ⚠️ INSEGURO - usar hashing
                    # Login exitoso con admin legacy
                    request.session['admin_logged'] = True
                    request.session['admin_id'] = admin.id
                    request.session['admin_username'] = admin.usuario
                    request.session['admin_name'] = admin.nombre
                    request.session['is_django_user'] = False
                    
                    return Response({
                        'success': True,
                        'message': 'Login exitoso',
                        'user': {
                            'id': admin.id,
                            'username': admin.usuario,
                            'nombre': admin.nombre,
                            'email': admin.correo,
                            'is_superuser': False,
                            'is_staff': False,
                            'categoria': None,
                            'is_legacy': True
                        }
                    })
                
            except AdminDenuncias.DoesNotExist:
                pass
            
            # Credenciales inválidas
            return Response({
                'success': False,
                'message': 'Usuario o contraseña incorrectos'
            }, status=401)
            
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'message': 'Formato de datos inválido'
            }, status=400)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error en login: {str(e)}'
            }, status=500)
    
    def _handle_logout(self, request):
        """
        Maneja el logout de administradores
        """
        try:
            # Si es usuario Django autenticado
            if request.user.is_authenticated:
                logout(request)
            
            # Limpiar sesión
            session_keys = [
                'admin_logged', 'admin_id', 'admin_username', 
                'admin_name', 'is_django_user'
            ]
            for key in session_keys:
                request.session.pop(key, None)
            
            return Response({
                'success': True,
                'message': 'Sesión cerrada exitosamente'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al cerrar sesión: {str(e)}'
            }, status=500)
    
    def _handle_check_auth(self, request):
        """
        Verifica el estado de autenticación del usuario
        """
        try:
            # Verificar si hay usuario Django autenticado
            if request.user.is_authenticated:
                user_data = {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'is_superuser': request.user.is_superuser,
                    'is_staff': request.user.is_staff,
                }
                
                # Agregar categoría si existe
                if hasattr(request.user, 'rol_categoria') and request.user.rol_categoria:
                    user_data['categoria'] = {
                        'id': request.user.rol_categoria.id,
                        'nombre': request.user.rol_categoria.nombre
                    }
                else:
                    user_data['categoria'] = None
                
                return Response({
                    'authenticated': True,
                    'is_admin': True,
                    'user': user_data
                })
            
            # Verificar sesión legacy
            if request.session.get('admin_logged'):
                return Response({
                    'authenticated': True,
                    'is_admin': True,
                    'user': {
                        'id': request.session.get('admin_id'),
                        'username': request.session.get('admin_username'),
                        'nombre': request.session.get('admin_name'),
                        'is_legacy': not request.session.get('is_django_user', False)
                    }
                })
            
            # No autenticado
            return Response({
                'authenticated': False,
                'is_admin': False,
                'user': None
            })
            
        except Exception as e:
            return Response({
                'authenticated': False,
                'is_admin': False,
                'error': str(e)
            }, status=500)