import random
import string
import re
from django.core.exceptions import ValidationError




def validate_admin_password(password):
    """Validador de contraseña estricto para admins"""
    if len(password) < 8:
        raise ValidationError('La contraseña debe tener al menos 8 caracteres')
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError('La contraseña debe tener al menos una letra mayúscula')
    
    if not re.search(r'[0-9]', password):
        raise ValidationError('La contraseña debe tener al menos un número')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError('La contraseña debe tener al menos un símbolo (!@#$%^&*(),.?":{}|<>)')



def generate_user_id():
    """Genera un ID único de 5 caracteres alfanuméricos"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def generate_denuncia_code():
    """Genera código de denuncia único"""
    return f"DN-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"

def validate_rut(rut):
    """Validador de RUT chileno"""
    # Remover puntos y guión para validación
    clean_rut = re.sub(r'[.-]', '', rut)
    
    if len(clean_rut) < 8 or len(clean_rut) > 9:
        raise ValidationError('RUT debe tener entre 8 y 9 dígitos')
    
    # Extraer número y dígito verificador
    numero = clean_rut[:-1]
    dv = clean_rut[-1].upper()
    
    # Calcular dígito verificador
    suma = 0
    multiplo = 2
    
    for digit in reversed(numero):
        suma += int(digit) * multiplo
        multiplo += 1
        if multiplo == 8:
            multiplo = 2
    
    resto = suma % 11
    dv_calculado = 11 - resto
    
    if dv_calculado == 11:
        dv_calculado = '0'
    elif dv_calculado == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(dv_calculado)
    
    if dv != dv_calculado:
        raise ValidationError('RUT inválido')