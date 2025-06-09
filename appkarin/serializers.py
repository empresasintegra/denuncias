from rest_framework import serializers
from .models import (
    Tiempo, Categoria, Item, RelacionEmpresa, Usuario, Denuncia, 
    Archivo, Foro, AdminDenuncias,DenunciaEstado, EstadosDenuncia,
    validate_rut, validate_admin_password
)
import re


# =================================================================
# SERIALIZERS BÁSICOS (Para modelos simples)
# =================================================================

class TiempoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tiempo
        fields = ['id', 'intervalo']


class CategoriaSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    def get_items_count(self, obj):
        return obj.item_set.count()
    
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'items_count']


class ItemSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    
    class Meta:
        model = Item
        fields = ['id', 'enunciado', 'categoria', 'categoria_nombre']


class RelacionEmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelacionEmpresa
        fields = ['id', 'rol']


class DenunciaEstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DenunciaEstado
        fields = ['id', 'estado']


# =================================================================
# SERIALIZERS DE USUARIO (Con validaciones complejas)
# =================================================================

class RutValidationSerializer(serializers.Serializer):
    """Serializer específico para validación de RUT"""
    
    rut = serializers.CharField(
        max_length=12,
        help_text="RUT en formato 12345678-9"
    )
    
    def validate_rut(self, value):
        """Validar formato de RUT"""
        if not value or not value.strip():
            raise serializers.ValidationError("RUT es requerido")
        
        try:
            validate_rut(value.strip())
            return value.strip()
        except Exception as e:
            raise serializers.ValidationError(str(e))



class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios (anónimos o identificados)"""
    
    # Campos opcionales que se requieren solo para usuarios identificados
    rut = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="RUT chileno formato: 12345678-9"
    )
    nombre = serializers.CharField(
        required=False, 
        allow_blank=True,
        max_length=250
    )
    apellidos = serializers.CharField(
        required=False, 
        allow_blank=True,
        max_length=250
    )
    correo = serializers.EmailField(
        required=False, 
        allow_blank=True,
        max_length=250
    )
    celular = serializers.CharField(
        required=False, 
        allow_blank=True,
        max_length=15,
        help_text="Formato: +56912345678"
    )
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'anonimo', 'rut', 'nombre', 'apellidos', 
            'correo', 'celular', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']
    
    def validate_rut(self, value):
        """Validar RUT solo si se proporciona"""
        if value and value.strip():
            try:
                validate_rut(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_celular(self, value):
        """Validar formato de celular chileno"""
        if value and value.strip():
            # Limpiar formato para validación
            clean_celular = re.sub(r'[^\d]', '', value)
            if len(clean_celular) == 8:
                # Formato interno: +569XXXXXXXX
                return f"+569{clean_celular}"
            elif len(clean_celular) == 11 and clean_celular.startswith('569'):
                return f"+{clean_celular}"
            elif len(clean_celular) == 9 and clean_celular.startswith('9'):
                return f"+56{clean_celular}"
            else:
                raise serializers.ValidationError(
                    "Formato inválido. Use: 912345678 o +56912345678"
                )
        return value
    
    def validate(self, data):
        """Validación a nivel de objeto"""
        anonimo = data.get('anonimo', True)
        
        if not anonimo:
            # Para usuarios identificados, validar campos requeridos
            required_fields = ['rut', 'nombre', 'apellidos', 'correo']
            for field in required_fields:
                if not data.get(field) or not data.get(field).strip():
                    raise serializers.ValidationError({
                        field: f'{field} es requerido para usuarios no anónimos'
                    })
        else:
            # Para usuarios anónimos, limpiar campos innecesarios
            data['rut'] = None
            data['nombre'] = None
            data['apellidos'] = None
            data['correo'] = None
            data['celular'] = None
        
        return data
    
    def update_or_create(self):
        """
        Usa update_or_create de Django para simplificar
        """
        rut = self.validated_data.get('rut')
        
        if rut and not self.validated_data.get('anonimo', True):
            # Para usuarios identificados, buscar por RUT
            usuario, created = Usuario.objects.update_or_create(
                rut=rut,  # Campo de búsqueda
                defaults=self.validated_data  # Campos a actualizar/crear
            )
            
            if created:
                print(f"✅ Usuario creado con RUT: {rut} - ID: {usuario.id}")
            else:
                print(f"✅ Usuario actualizado con RUT: {rut} - ID: {usuario.id}")
            
            return usuario
        else:
            # Para usuarios anónimos, siempre crear nuevo
            usuario = Usuario.objects.create(**self.validated_data)
            print(f"✅ Usuario anónimo creado: {usuario.id}")
            return usuario


class UsuarioDetailSerializer(serializers.ModelSerializer):
    """Serializer para mostrar detalles del usuario"""
    nombre_completo = serializers.ReadOnlyField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'anonimo', 'rut', 'nombre', 'apellidos', 'correo', 
            'celular', 'nombre_completo', 'fecha_creacion', 'ultima_actividad'
        ]


# =================================================================
# SERIALIZERS DE DENUNCIA (Complejos con múltiples relaciones)
# =================================================================

class DenunciaCreateSerializer(serializers.Serializer):
    """Serializer para crear denuncias a través del wizard"""
    
    # Paso 1: Relación empresa
    denuncia_relacion = serializers.IntegerField()
    descripcion_relacion = serializers.CharField(
        required=False, 
        allow_blank=True, 
        max_length=50,
        help_text="Requerido solo si relación es 'Otro'"
    )
    
    # Paso 2: Tiempo
    denuncia_tiempo = serializers.IntegerField()
    
    # Paso 3: Descripción
    descripcion = serializers.CharField(
        min_length=50, 
        max_length=2000,
        error_messages={
            'min_length': 'La descripción debe tener al menos 50 caracteres',
            'max_length': 'La descripción no puede exceder 2000 caracteres',
            'required': 'La descripción es obligatoria'
        }
    )
    
    # Datos del item (desde sesión)
    item_id = serializers.IntegerField(write_only=True)
    
    def validate_denuncia_relacion(self, value):
        """Validar que la relación empresa existe"""
        try:
            RelacionEmpresa.objects.get(id=value)
        except RelacionEmpresa.DoesNotExist:
            raise serializers.ValidationError('Relación con empresa no válida')
        return value
    
    def validate_denuncia_tiempo(self, value):
        """Validar que el tiempo existe"""
        try:
            Tiempo.objects.get(id=value)
        except Tiempo.DoesNotExist:
            raise serializers.ValidationError('Tiempo de denuncia no válido')
        return value
    
    def validate_item_id(self, value):
        """Validar que el item existe"""
        try:
            Item.objects.get(id=value)
        except Item.DoesNotExist:
            raise serializers.ValidationError('Tipo de denuncia no válido')
        return value
    
    def validate(self, data):
        """Validación cruzada"""
        # Validar descripción_relacion si es necesaria
        print("validate")
        relacion_id = data.get('denuncia_relacion')
        print(relacion_id)
        if relacion_id:
            try:
                relacion = RelacionEmpresa.objects.get(id=relacion_id)
                if relacion.rol.lower() == 'otro':
                    descripcion_relacion = data.get('descripcion_relacion', '').strip()
                    if not descripcion_relacion:
                        raise serializers.ValidationError({
                            'descripcion_relacion': 'Debe especificar su relación con la empresa'
                        })
                    elif len(descripcion_relacion) < 3:
                        raise serializers.ValidationError({
                            'descripcion_relacion': 'La descripción debe tener al menos 3 caracteres'
                        })
            except RelacionEmpresa.DoesNotExist:
                pass  # Ya validado en validate_denuncia_relacion

    def update_or_create(self):
        """
        Usa update_or_create de Django para simplificar
         """
        codigo = self.validated_data.get('codigo')
        
            # Para usuarios identificados, buscar por RUT
        denuncia, created = Denuncia.objects.update_or_create(
                codigo=codigo,  # Campo de búsqueda
                defaults=self.validated_data  # Campos a actualizar/crear
            )
            
        if created:
            print(f"✅ Denuncia creada con RUT: {codigo} - codigo: {denuncia.codigo}")
        else:
            print(f"✅ Denuncia actualizada con RUT: {codigo} - Codigo: {denuncia.codigo}")
            
        return denuncia


class DenunciaListSerializer(serializers.ModelSerializer):
    """Serializer para listar denuncias con datos relacionados"""
    
    usuario_nombre = serializers.SerializerMethodField()
    item_enunciado = serializers.CharField(source='item.enunciado', read_only=True)
    categoria_nombre = serializers.CharField(source='item.categoria.nombre', read_only=True)
    relacion_empresa_rol = serializers.CharField(source='relacion_empresa.rol', read_only=True)
    tiempo_intervalo = serializers.CharField(source='tiempo.intervalo', read_only=True)
    fecha_formateada = serializers.SerializerMethodField()
    
    def get_usuario_nombre(self, obj):
        if obj.usuario.anonimo:
            return f"Usuario Anónimo ({obj.usuario.id})"
        return obj.usuario.nombre_completo
    
    def get_fecha_formateada(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    
    class Meta:
        model = Denuncia
        fields = [
            'codigo', 'usuario_nombre', 'item_enunciado', 'categoria_nombre',
            'relacion_empresa_rol', 'tiempo_intervalo', 'estado_actual',
            'fecha_formateada', 'fecha'
        ]


class DenunciaDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles completos de denuncia"""
    
    usuario = UsuarioDetailSerializer(read_only=True)
    item = ItemSerializer(read_only=True)
    relacion_empresa = RelacionEmpresaSerializer(read_only=True)
    tiempo = TiempoSerializer(read_only=True)
    archivos = serializers.SerializerMethodField()
    mensajes_foro = serializers.SerializerMethodField()
    estados_historial = serializers.SerializerMethodField()
    
    def get_archivos(self, obj):
        return [archivo.url for archivo in obj.archivo_set.all()]
    
    def get_mensajes_foro(self, obj):
        mensajes = obj.foro_set.all().order_by('id')
        return [{
            'id': m.id,
            'mensaje': m.mensaje,
            'es_admin': m.admin is not None,
            'admin_nombre': m.admin.nombre if m.admin else None
        } for m in mensajes]
    
    def get_estados_historial(self, obj):
        estados = obj.estadosdenuncia_set.all().order_by('fecha')
        return [{
            'estado': estado.estado.estado,
            'fecha': estado.fecha.strftime('%d/%m/%Y %H:%M')
        } for estado in estados]
    
    class Meta:
        model = Denuncia
        fields = [
            'codigo', 'usuario', 'item', 'relacion_empresa', 'tiempo',
            'descripcion', 'descripcion_relacion', 'estado_actual',
            'fecha', 'fecha_actualizacion', 'archivos', 'mensajes_foro',
            'estados_historial'
        ]


# =================================================================
# SERIALIZERS DE ARCHIVOS
# =================================================================

class ArchivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Archivo
        fields = ['id', 'denuncia', 'url']


class ArchivoCreateSerializer(serializers.ModelSerializer):
    """Serializer para subir archivos a denuncias"""
    
    class Meta:
        model = Archivo
        fields = ['denuncia', 'url']
    
    def validate_url(self, value):
        """Validar que la URL es válida"""
        if not value.startswith(('http://', 'https://', '/')):
            raise serializers.ValidationError('URL de archivo inválida')
        return value




# =================================================================
# SERIALIZERS DE FORO
# =================================================================

class ForoSerializer(serializers.ModelSerializer):
    admin_nombre = serializers.CharField(source='admin.nombre', read_only=True)
    es_admin = serializers.SerializerMethodField()
    
    def get_es_admin(self, obj):
        return obj.admin is not None
    
    class Meta:
        model = Foro
        fields = ['id', 'denuncia', 'admin', 'admin_nombre', 'mensaje', 'es_admin']


class ForoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear mensajes en el foro"""
    
    class Meta:
        model = Foro
        fields = ['denuncia', 'admin', 'mensaje']
    
    def validate_mensaje(self, value):
        if not value.strip():
            raise serializers.ValidationError('El mensaje no puede estar vacío')
        if len(value.strip()) < 10:
            raise serializers.ValidationError('El mensaje debe tener al menos 10 caracteres')
        return value.strip()


# =================================================================
# SERIALIZERS DE ESTADOS
# =================================================================

class EstadosDenunciaSerializer(serializers.ModelSerializer):
    estado_nombre = serializers.CharField(source='estado.estado', read_only=True)
    fecha_formateada = serializers.SerializerMethodField()
    
    def get_fecha_formateada(self, obj):
        return obj.fecha.strftime('%d/%m/%Y %H:%M')
    
    class Meta:
        model = EstadosDenuncia
        fields = ['id', 'denuncia', 'estado', 'estado_nombre', 'fecha', 'fecha_formateada']


# =================================================================
# SERIALIZERS ESPECIALIZADOS PARA TU FRONTEND
# =================================================================

class CategoriaWithItemsSerializer(serializers.ModelSerializer):
    """Serializer para la página de items con categorías expandidas"""
    items = ItemSerializer(source='item_set', many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    
    def get_items_count(self, obj):
        return obj.item_set.count()
    
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'items', 'items_count']


class DenunciaWizardDataSerializer(serializers.Serializer):
    """Serializer para cargar datos del wizard"""
    categorias = CategoriaWithItemsSerializer(many=True, read_only=True)
    relacion_empresas = RelacionEmpresaSerializer(many=True, read_only=True)
    tiempos = TiempoSerializer(many=True, read_only=True)


class ConsultaDenunciaSerializer(serializers.Serializer):
    """Serializer para consultas de denuncia por código"""
    codigo = serializers.CharField(
        max_length=11,
        help_text="Código de denuncia: DN-XXXXXXXX o XXXXX"
    )
    
    def validate_codigo(self, value):
        """Validar formato de código"""
        codigo_clean = value.strip().upper()
        
        # Validar formato DN-XXXXXXXX o XXXXX
        if not (re.match(r'^DN-[A-Z0-9]{8}$', codigo_clean) or 
                re.match(r'^[A-Z0-9]{5}$', codigo_clean)):
            raise serializers.ValidationError(
                'Formato inválido. Use: DN-XXXXXXXX o XXXXX'
            )
        
        return codigo_clean
    

class ItemSelectionSerializer(serializers.Serializer):
    """Serializer específico para selección de items"""
    denuncia_item = serializers.IntegerField(
        help_text="ID del item de denuncia seleccionado"
    )
    
    def validate_denuncia_item(self, value):
        """Validar que el item existe"""
        try:
            item = Item.objects.select_related('categoria').get(id=value)
            # Guardar el item validado para uso posterior
            self._validated_item = item
            return value
        except Item.DoesNotExist:
            raise serializers.ValidationError("Tipo de denuncia no válido")
    
    def get_validated_item(self):
        """Obtener el item validado"""
        return getattr(self, '_validated_item', None)
