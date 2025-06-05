from django.db import models
import random
import string
import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator




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


class Tiempo(models.Model):
    intervalo=models.CharField(max_length=250)
    
    class Meta:
        verbose_name = "Tiempo"
        verbose_name_plural = "Tiempos"


# Create your models here.
class Categoria(models.Model):
    nombre=models.CharField(max_length=250) 

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    


class Item(models.Model):
    enunciado = models.CharField(max_length=500)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"


class RelacionEmpresa(models.Model):
    rol = models.CharField(max_length=500)

    class Meta:
        verbose_name = "Relacion_empresa"
        verbose_name_plural = "Relaciones_empresa"

class Usuario(models.Model):
    # PK siempre random para consistencia
    id = models.CharField(
        max_length=5, 
        primary_key=True, 
        default=generate_user_id,
        editable=False,
        unique=True,
        help_text="ID único de 5 caracteres generado automáticamente"
    )
    
    # Tipo de usuario
    anonimo = models.BooleanField(
        default=True,
        help_text="Si es True, solo se requiere el ID. Si es False, se requieren datos personales."
    )
    
    # CAMPOS PARA USUARIOS IDENTIFICADOS
    rut = models.CharField(
        max_length=12,
        unique=True,
        blank=True,
        null=True,
        validators=[validate_rut],
        help_text="RUT chileno (formato: 12345678-9 o 12.345.678-9)"
    )
    
    nombre = models.CharField(
        max_length=250, 
        blank=True, 
        null=True,
        help_text="Requerido para usuarios no anónimos"
    )
    
    apellidos = models.CharField(
        max_length=250, 
        blank=True, 
        null=True,
        help_text="Requerido para usuarios no anónimos"
    )
    
    correo = models.EmailField(
        max_length=250, 
        blank=True, 
        null=True,
        help_text="Requerido para usuarios no anónimos"
    )
    
    celular = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?56?[0-9]{8,9}$',
            message='Formato: +56912345678 o 912345678'
        )],
        help_text="Número de celular chileno"
    )
    
    # CAMPOS DE CONTROL
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_actividad = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        if not self.anonimo:
            # Para usuarios identificados, todos los campos son requeridos
            required_fields = ['rut', 'nombre', 'apellidos', 'correo']
            for field in required_fields:
                if not getattr(self, field):
                    raise ValidationError(f'{field} es requerido para usuarios no anónimos')
        else:
            # Para usuarios anónimos, limpiar campos innecesarios
            self.rut = None
            self.nombre = None
            self.apellidos = None
            self.correo = None
            self.celular = None

    def save(self, *args, **kwargs):
        # Generar ID único si no existe
        if not self.id:
            while True:
                new_id = generate_user_id()
                if not Usuario.objects.filter(id=new_id).exists():
                    self.id = new_id
                    break
        
        # Limpiar y formatear RUT
        if self.rut:
            self.rut = re.sub(r'[.-]', '', self.rut)
            # Reformatear: 123456789 -> 12.345.678-9
            if len(self.rut) == 9:
                self.rut = f"{self.rut[:2]}.{self.rut[2:5]}.{self.rut[5:8]}-{self.rut[8]}"
            elif len(self.rut) == 8:
                self.rut = f"{self.rut[:1]}.{self.rut[1:4]}.{self.rut[4:7]}-{self.rut[7]}"
        
        # Validar antes de guardar
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.anonimo:
            return f"Usuario Anónimo ({self.id})"
        else:
            return f"{self.nombre} {self.apellidos} ({self.rut}) - ID: {self.id}"

    @property
    def nombre_completo(self):
        if self.anonimo:
            return f"Usuario Anónimo {self.id}"
        return f"{self.nombre} {self.apellidos}"

# =================================================================
# MODELO DENUNCIA ACTUALIZADO
# =================================================================

class Denuncia(models.Model):
    # Código único por denuncia
    codigo = models.CharField(
        max_length=11,  # DN-XXXXXXXX
        primary_key=True,
        default=generate_denuncia_code,
        editable=False,
        help_text="Código único de seguimiento de la denuncia"
    )
    
    # Relaciones
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    relacion_empresa = models.ForeignKey('RelacionEmpresa', on_delete=models.CASCADE)
    tiempo = models.ForeignKey('Tiempo', on_delete=models.CASCADE)
    
    # Contenido
    descripcion = models.TextField(max_length=2000)
    descripcion_relacion= models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Descripción condicional a relacion empresa 'Otro' "
    )

    # Timestamps
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Estado
    estado_actual = models.CharField(
        max_length=50, 
        default='PENDIENTE',
        choices=[
            ('PENDIENTE', 'Pendiente'),
            ('EN_REVISION', 'En Revisión'),
            ('RESUELTO', 'Resuelto'),
        ]
    )
    
    class Meta:
        verbose_name = "Denuncia"
        verbose_name_plural = "Denuncias"
        ordering = ['-fecha']
    
    def save(self, *args, **kwargs):
        # Generar código único si no existe
        if not self.codigo:
            while True:
                new_code = generate_denuncia_code()
                if not Denuncia.objects.filter(codigo=new_code).exists():
                    self.codigo = new_code
                    break
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Denuncia {self.codigo} - {self.usuario.nombre_completo}"

class Archivo(models.Model):
    denuncia=models.ForeignKey(Denuncia, on_delete=models.CASCADE)
    url=models.URLField(max_length=500)
    nombre=models.CharField(max_length=250)
    descripción=models.CharField(max_length=250)
    Peso=models.IntegerField()

    class Meta:
        verbose_name = "Archivo"
        verbose_name_plural = "Archivos"


class Admin(models.Model):
   
    rut = models.CharField(max_length=12, unique=True, blank=True, null=True, validators=[validate_rut])
    nombre = models.CharField(max_length=250)
    apellidos = models.CharField(max_length=250)
    correo = models.EmailField(max_length=250, unique=True)
    contraseña = models.CharField(max_length=250, validators=[validate_admin_password])


    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"


class Foro(models.Model):
    denuncia=models.ForeignKey(Denuncia, on_delete=models.CASCADE)
    admin = models.ForeignKey(
        Admin,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Administrador que escribió el mensaje (null si fue el usuario)"
    )
    mensaje=models.TextField(max_length=2000)

    class Meta:
        verbose_name = "Foro"
        verbose_name_plural = "Foros"


class DenunciaEstado(models.Model):
    
    estado = models.CharField(max_length=250)
    class Meta:
        verbose_name = "Estado de la denuncia"
        verbose_name_plural = "Estados de las denuncias"


class EstadosDenuncia(models.Model):
    denuncia=models.ForeignKey(Denuncia, on_delete=models.CASCADE)
    estado=models.ForeignKey(DenunciaEstado, on_delete=models.CASCADE)
    fecha=models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Estado de denuncia"
        verbose_name_plural = "Estados de denuncias"
    




