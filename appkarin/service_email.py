# service_email.py - Servicio de envío de emails con fecha/hora
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.shortcuts import redirect
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from appkarin.emailSDK.email_sdk import EmailSDK
from .models import Categoria
from datetime import datetime, timedelta
from .models import AdminDenuncias

@method_decorator(csrf_exempt, name='dispatch')
class EmailSenderAPIView(APIView):
    """
    Servicio para envío de emails de confirmación de denuncias.
    """
    
    def post(self, request, action=None):
        """
        POST /api/email/send/  
        """
        try:
            print("Iniciando proceso de envío de email...")
            print('Datos recibidos:', request.data)
            # ✅ Obtener email
            if request.data.get('correo_electronico'):
                email = request.data.get('correo_electronico')
            else:
                response_data = {
                'success': True,
                'message': 'Anonimo',
                'redirect_url': '/denuncia/final/'
                }

                return Response(response_data)
            

            # ✅ Obtener fecha y hora actual (hora de Chile aproximada)
            # Chile está UTC-3 (horario estándar) o UTC-4 (horario de verano)
            ahora = datetime.now()
            
            # ✅ Formatear componentes de fecha/hora
            dia = ahora.day
            anio = ahora.year
            hora = ahora.strftime('%H:%M')  # Formato 24 horas: HH:MM
            
            # ✅ Meses en español
            meses = [
                '', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
            ]
            mes = meses[ahora.month]
            
            # ✅ Código de denuncia (puedes obtenerlo del request o generar uno temporal)

            
            codigo = request.session.get('codigo')

            # Verificar que el código exista
            if not codigo:
                print("❌ Error: No se encontró código en sesión")
                return Response({
                    'success': False,
                    'message': 'Error: No se pudo obtener el código de denuncia',
                    'redirect_url': '/denuncia/Paso1/'
                }, status=400)
            
            # ✅ Debug de fecha/hora
            print(f"📅 Fecha: {dia} de {mes} de {anio}")
            print(f"🕐 Hora: {hora}")
            print(f"🎫 Código: {codigo}")
            
            # ✅ Template HTML con variables formateadas
            template_html = f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
                <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #28a745; text-align: center; margin-bottom: 30px;">
                        ✅ Denuncia Registrada Exitosamente
                    </h1>
                    
                    <p style="font-size: 16px; line-height: 1.6; color: #333;">
                        Su denuncia ha sido ingresada correctamente en nuestro sistema.
                    </p>
                    
                    <div style="background-color: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #155724; margin-top: 0;">📋 Detalles de su denuncia:</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li style="margin: 10px 0;"><strong>🎫 Código de Denuncia:</strong> {codigo}</li>
                            <li style="margin: 10px 0;"><strong>📅 Fecha de Registro:</strong> {dia} de {mes} de {anio}</li>
                            <li style="margin: 10px 0;"><strong>🕐 Hora:</strong> {hora}</li>
                            <li style="margin: 10px 0;"><strong>📊 Estado:</strong> En Proceso de Revisión</li>
                        </ul>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                        <p style="margin: 0; color: #856404;">
                            <strong>📝 Importante:</strong> Guarde este código para futuras consultas sobre el estado de su denuncia.
                        </p>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; text-align: center; margin-top: 30px;">
                        Empresas Integra - Sistema de Denuncias<br>
                        Este es un mensaje automático, no responda a este correo.
                    </p>
                </div>
            </div>
            '''

            id=request.session.get('denuncia_categoria_id')
            print('Categoria ID:', id)
            Administradores=AdminDenuncias.objects.filter(rol_categoria__id=id)
            
            print('Administradores a notificar:', Administradores)
            cc=[]

            for admin in Administradores:
                cc.append(admin.email)

            # ✅ Crear y enviar email
            emailSDK = EmailSDK(
                email,
                'Denuncia Registrada - Empresas Integra',  # Asunto más descriptivo
                template_html,
                "soporte@empresasintegra.onmicrosoft.com",
                cc=cc
            )
            
            emailSDK.send_mail()
            print("email enviado")
            print('Email enviado a:', email)
            print('email que envía',emailSDK.sender)
            response_data = {
                'success': True,
                'message': 'Email enviado correctamente',
                'email_sent_to': email,
                'fecha_envio': f"{dia} de {mes} de {anio} a las {hora}",
                'codigo_denuncia': codigo,
                'redirect_url': '/denuncia/final/'
            }

            return Response(response_data)
                
        except Exception as e:
            print(f"❌ Error enviando email: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error enviando email: {str(e)}'
            }, status=500)