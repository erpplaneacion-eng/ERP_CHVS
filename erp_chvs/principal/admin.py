from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    PerfilUsuario,
    PrincipalDepartamento,
    PrincipalMunicipio,
    RegistroActividad,
    TipoDocumento,
    TipoGenero,
    ModalidadesDeConsumo,
    NivelGradoEscolar,
    TablaGradosEscolaresUapa
)

# Definir el inline para PerfilUsuario
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'
    extra = 0
    max_num = 1

# Extender el UserAdmin nativo
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)

    # Widget mejorado para selección múltiple de grupos y permisos
    filter_horizontal = ('groups', 'user_permissions')

    # Configuración de fieldsets para mejor organización
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos y Accesos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Un usuario puede pertenecer a múltiples grupos. Seleccione todos los que apliquen.'
        }),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

    def get_inline_instances(self, request, obj=None):
        # En la vista de creación, el perfil lo crea la señal post_save.
        # Evitamos que el inline intente crear un segundo PerfilUsuario.
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

# Re-registrar User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register your models here.
@admin.register(PrincipalDepartamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('codigo_departamento', 'nombre_departamento')
    search_fields = ('nombre_departamento', 'codigo_departamento')
    
@admin.register(PrincipalMunicipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo_municipio', 'nombre_municipio', 'codigo_departamento')
    search_fields = ('nombre_municipio', 'codigo_municipio')

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('id_documento', 'tipo_documento', 'codigo_documento')
    search_fields = ('tipo_documento', 'id_documento')
    list_filter = ('codigo_documento',)

@admin.register(TipoGenero)
class TipoGeneroAdmin(admin.ModelAdmin):
    list_display = ('id_genero', 'genero', 'codigo_genero')
    search_fields = ('genero', 'id_genero')
    list_filter = ('codigo_genero',)

@admin.register(ModalidadesDeConsumo)
class ModalidadesDeConsumoAdmin(admin.ModelAdmin):
    list_display = ('id_modalidades', 'modalidad', 'cod_modalidad')
    search_fields = ('modalidad', 'id_modalidades', 'cod_modalidad')
    list_filter = ('cod_modalidad',)

@admin.register(NivelGradoEscolar)
class NivelGradoEscolarAdmin(admin.ModelAdmin):
    list_display = ('id_grado_escolar', 'grados_sedes', 'nivel_escolar_uapa')
    search_fields = ('id_grado_escolar', 'grados_sedes', 'nivel_escolar_uapa__nivel_escolar_uapa')
    list_filter = ('nivel_escolar_uapa',)
    autocomplete_fields = ['nivel_escolar_uapa']

@admin.register(TablaGradosEscolaresUapa)
class TablaGradosEscolaresUapaAdmin(admin.ModelAdmin):
    list_display = ('id_grado_escolar_uapa', 'nivel_escolar_uapa')
    search_fields = ('id_grado_escolar_uapa', 'nivel_escolar_uapa')
    list_filter = ('nivel_escolar_uapa',)


@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'modulo', 'accion', 'descripcion_corta', 'ip', 'exitoso')
    list_filter = ('modulo', 'exitoso', 'usuario')
    search_fields = ('usuario__username', 'accion', 'descripcion', 'ip')
    date_hierarchy = 'fecha'
    readonly_fields = ('usuario', 'modulo', 'accion', 'descripcion', 'ip', 'fecha', 'exitoso')
    ordering = ('-fecha',)

    def descripcion_corta(self, obj):
        return obj.descripcion[:80] + '…' if len(obj.descripcion) > 80 else obj.descripcion
    descripcion_corta.short_description = 'Detalle'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
