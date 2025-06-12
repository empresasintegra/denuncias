from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .utils import (
                    validate_admin_password, validate_rut,generate_user_id, 
                    generate_denuncia_code,validate_rut,
                    )
import re




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

class Empresa(models.Model):
    nombre = models.CharField(
        max_length=250, 
        help_text="nombre de la empresa asociada a Integra"
    )
    descripcion= models.TextField(max_length=500)


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
    tipo_empresa= models.ForeignKey(Empresa, on_delete=models.CASCADE)
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
    Peso = models.IntegerField(
        default=0,  # Valor por defecto para archivos existentes
        help_text="Peso del archivo en bytes"
    )

    class Meta:
        verbose_name = "Archivo"
        verbose_name_plural = "Archivos"


class AdminDenuncias(AbstractUser):
   
    rut = models.CharField(max_length=12, unique=True, blank=True, null=True, validators=[validate_rut])
    rol_categoria=models.ForeignKey(Categoria,blank=True,null=True, on_delete=models.CASCADE)
    _password_to_validate = None

    class Meta:
        verbose_name = "Administrador de Denuncias"
        verbose_name_plural = "Administradores de Denuncias"

    def clean(self):
        """Validaciones personalizadas incluyendo contraseña"""
        super().clean()
        
        # Validar contraseña si hay una nueva
        if hasattr(self, '_password_to_validate') and self._password_to_validate:
            try:
                validate_admin_password(self._password_to_validate)
            except ValidationError as e:
                raise ValidationError({'password': e.message})
    
    def set_password(self, raw_password):
        """Sobrescribir para validar antes de establecer la contraseña"""
        if raw_password:
            # Guardar temporalmente para validar en clean()
            self._password_to_validate = raw_password
            
            # Validar inmediatamente
            validate_admin_password(raw_password)
        
        # Llamar al método padre para encriptar y guardar
        super().set_password(raw_password)


class Foro(models.Model):
    denuncia=models.ForeignKey(Denuncia, on_delete=models.CASCADE)
    admin = models.ForeignKey(
        AdminDenuncias,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Administrador que escribió el mensaje (null si fue el usuario)"
    )
    mensaje=models.TextField(max_length=2000)
    leido= models.BooleanField(
        null=True,
        help_text="Boleano que indica si son mensajes obsoletos o no, si es null va ser el primer mensaje de cualquiera de los 2, y despues continua el ping-pong"
    )

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
    




