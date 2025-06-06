from django.contrib import admin
from .models import (
    Tiempo, Categoria, Item, RelacionEmpresa, Usuario, 
    Denuncia, Archivo,Foro, 
    DenunciaEstado, EstadosDenuncia
)

# Register your models here.

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(Tiempo)
class TiempoAdmin(admin.ModelAdmin):
    list_display = ['intervalo']
    search_fields = ['intervalo']
    ordering = ['intervalo']

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['enunciado', 'categoria']
    list_filter = ['categoria']
    search_fields = ['enunciado']
    ordering = ['categoria', 'enunciado']

@admin.register(RelacionEmpresa)
class RelacionEmpresaAdmin(admin.ModelAdmin):
    list_display = ['rol']
    search_fields = ['rol']
    ordering = ['rol']

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_completo', 'anonimo', 'rut', 'correo', 'fecha_creacion']
    list_filter = ['anonimo', 'fecha_creacion']
    search_fields = ['id', 'nombre', 'apellidos', 'rut', 'correo']
    readonly_fields = ['id', 'fecha_creacion', 'ultima_actividad']
    ordering = ['-fecha_creacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'anonimo')
        }),
        ('Datos Personales', {
            'fields': ('rut', 'nombre', 'apellidos', 'correo', 'celular'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'ultima_actividad'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'usuario', 'item', 'estado_actual', 'fecha']
    list_filter = ['estado_actual', 'fecha', 'item__categoria', 'relacion_empresa']
    search_fields = ['codigo', 'descripcion', 'usuario__nombre', 'usuario__apellidos']
    readonly_fields = ['codigo', 'fecha', 'fecha_actualizacion']
    ordering = ['-fecha']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'usuario', 'estado_actual')
        }),
        ('Detalles de la Denuncia', {
            'fields': ('item', 'relacion_empresa', 'descripcion_relacion', 'tiempo', 'descripcion')
        }),
        ('Fechas', {
            'fields': ('fecha', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Archivo)
class ArchivoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'denuncia', 'Peso', 'descripción']
    list_filter = ['denuncia__estado_actual']
    search_fields = ['nombre', 'descripción', 'denuncia__codigo']
    ordering = ['-denuncia__fecha']

@admin.register(Foro)
class ForoAdmin(admin.ModelAdmin):
    list_display = ['denuncia', 'admin', 'mensaje_corto']
    list_filter = ['admin', 'denuncia__estado_actual']
    search_fields = ['mensaje', 'denuncia__codigo']
    ordering = ['-id']
    
    def mensaje_corto(self, obj):
        return obj.mensaje[:50] + "..." if len(obj.mensaje) > 50 else obj.mensaje
    mensaje_corto.short_description = "Mensaje"

@admin.register(DenunciaEstado)
class DenunciaEstadoAdmin(admin.ModelAdmin):
    list_display = ['estado']
    search_fields = ['estado']
    ordering = ['estado']

@admin.register(EstadosDenuncia)
class EstadosDenunciaAdmin(admin.ModelAdmin):
    list_display = ['denuncia', 'estado', 'fecha']
    list_filter = ['estado', 'fecha']
    search_fields = ['denuncia__codigo']
    readonly_fields = ['fecha']
    ordering = ['-fecha']