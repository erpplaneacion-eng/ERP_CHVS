from django.contrib import admin
from .models import (
    PrincipalDepartamento,
    PrincipalMunicipio,
    TipoDocumento,
    TipoGenero,
    ModalidadesDeConsumo,
    NivelGradoEscolar,
    TablaGradosEscolaresUapa
)

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