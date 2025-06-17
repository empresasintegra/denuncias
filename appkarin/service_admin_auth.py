# service_admin_auth.py - Servicio consolidado para autenticación de administradores
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import AdminDenuncias
import json


@method_decorator(csrf_exempt, name='dispatch')
class ServiceAdminDenunciaAuth(APIView):
    """
    Servicio consolidado para todas las operaciones de autenticación de administradores.
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
            empresa = request.data.get('empresa')
            username = request.data.get('username', '').strip()
            password = request.data.get('password', '')
            
            if not username or not password:
                return Response({
                    'success': False,
                    'message': 'Usuario y contraseña son requeridos',
                    'error_code': 'MISSING_CREDENTIALS'
                }, status=400)
            
            # Primero intentar autenticación normal de Django
            print(f"🔐 Intentando autenticar a: {username}")
            user = authenticate(request, username=username, password=password)
            
            # Si la autenticación normal falla, verificar si es problema de contraseña no hasheada
            if user is None:
                print("❌ Autenticación normal falló, verificando contraseñas no hasheadas...")
                
                try:
                    # Buscar el usuario manualmente
                    admin_user = AdminDenuncias.objects.get(username=username)
                    
                    # Verificar si la contraseña está hasheada
                    is_hashed = admin_user.password.startswith(('pbkdf2_', 'bcrypt', 'argon2'))
                    
                    if not is_hashed:
                        print("⚠️ Contraseña en texto plano detectada")
                        
                        # Comparar contraseña en texto plano
                        if admin_user.password == password:
                            print("✅ Contraseña correcta, hasheando...")
                            
                            # Hashear la contraseña para futuras autenticaciones
                            admin_user.set_password(password)
                            admin_user.save()
                            print("✅ Contraseña hasheada y guardada")
                            
                            # Ahora intentar autenticar de nuevo
                            user = authenticate(request, username=username, password=password)
                        else:
                            print("❌ Contraseña incorrecta")
                    else:
                        # La contraseña está hasheada pero no coincide
                        print("❌ Contraseña hasheada pero incorrecta")
                        
                except AdminDenuncias.DoesNotExist:
                    print(f"❌ Usuario '{username}' no existe")
                except Exception as e:
                    print(f"❌ Error verificando usuario: {str(e)}")
            
            # Verificar el resultado final
            if user is not None:
                # Verificar que el usuario esté activo
                if not user.is_active:
                    return Response({
                        'success': False,
                        'message': 'Su cuenta está desactivada. Contacte al administrador.',
                        'error_code': 'USER_INACTIVE'
                    }, status=401)
                
                # Verificar que sea staff o superuser
                if not (user.is_staff or user.is_superuser):
                    print(f"⚠️ Usuario {username} no es staff. Actualizando...")
                    # Auto-corregir si no es staff
                    user.is_staff = True
                    user.save()
                
                # Login exitoso
                login(request, user)
                print(f"✅ Login exitoso para: {username}")
                
                # Preparar datos de respuesta
                response_data = {
                    'success': True,
                    'message': 'Login exitoso',
                    'user_info': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email or '',
                        'is_superuser': user.is_superuser,
                        'is_staff': user.is_staff,
                        'nombre_completo': user.get_full_name() or user.username
                    },
                    'redirect_url': f"/{empresa}/" if empresa else "/"
                }
                
                # Agregar información de categoría si existe
                if hasattr(user, 'rol_categoria') and user.rol_categoria:
                    response_data['user_info']['categoria'] = {
                        'id': user.rol_categoria.id,
                        'nombre': user.rol_categoria.nombre
                    }
                
                # Agregar RUT si existe
                if hasattr(user, 'rut') and user.rut:
                    response_data['user_info']['rut'] = user.rut
                
                # Guardar información en sesión
                request.session['admin_logged'] = True
                request.session['admin_id'] = user.id
                request.session['admin_username'] = user.username
                request.session['is_django_user'] = True
                request.session.save()
                
                return Response(response_data)
            
            # Si llegamos aquí, las credenciales son inválidas
            return Response({
                'success': False,
                'message': 'Usuario o contraseña incorrectos',
                'error_code': 'INVALID_CREDENTIALS'
            }, status=401)
            
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'message': 'Formato de datos inválido'
            }, status=400)
        except Exception as e:
            print(f"❌ Error en login: {str(e)}")
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
            
            request.session.save()
            
            return Response({
                'success': True,
                'message': 'Sesión cerrada exitosamente',
                'redirect_url': '/login/'
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
                    'email': request.user.email or '',
                    'is_superuser': request.user.is_superuser,
                    'is_staff': request.user.is_staff,
                    'nombre_completo': request.user.get_full_name() or request.user.username
                }
                
                # Agregar categoría si existe
                if hasattr(request.user, 'rol_categoria') and request.user.rol_categoria:
                    user_data['categoria'] = {
                        'id': request.user.rol_categoria.id,
                        'nombre': request.user.rol_categoria.nombre
                    }
                
                # Agregar RUT si existe
                if hasattr(request.user, 'rut') and request.user.rut:
                    user_data['rut'] = request.user.rut
                
                return Response({
                    'success': True,
                    'authenticated': True,
                    'is_admin': request.user.is_staff or request.user.is_superuser,
                    'user_info': user_data
                })
            
            # No autenticado
            return Response({
                'success': False,
                'authenticated': False,
                'is_admin': False,
                'user_info': None
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'authenticated': False,
                'is_admin': False,
                'error': str(e)
            }, status=500)