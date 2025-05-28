from django.db import models



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

class Usuario(models.Model):
    anonimo=models.BooleanField(default=True)
    nombre = models.CharField(max_length=250)
    apellidos=models.CharField(max_length=250)
    correo=models.EmailField(max_length=250)
    celular=models.IntegerField()
    #fecha_creacion = models.DateTimeField(auto_now_add=True)
    #ultima_actividad = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

class Denuncia(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    relacion_empresa=models.ForeignKey(RelacionEmpresa, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=2000) #descripción de los hechos
    fecha=models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['usuario_id','item_id','relacion_empresa_id']]  # Evitar duplicados
        verbose_name = "Denuncia"
        verbose_name_plural = "Denuncias"

class Archivo(models.Model):
    denuncia=models.ForeignKey(Denuncia, on_delete=models.CASCADE)
    url=models.URLField(max_length=500)

    class Meta:
        verbose_name = "archivo"
        verbose_name_plural = "archivos"

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
    




