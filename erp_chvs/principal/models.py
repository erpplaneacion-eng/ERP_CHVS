import logging

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# Create your models here.

class PerfilUsuario(models.Model):
    SEDE_CHOICES = [
        ('CALI', 'Cali'),
        ('YUMBO', 'Yumbo'),
        ('AMBAS', 'Ambas'),
    ]
    
    MODULO_CHOICES = [
        ('NUTRICION', 'Nutrición'),
        ('FACTURACION', 'Facturación'),
        ('PLANEACION', 'Planeación'),
        ('ADMINISTRACION', 'Administración'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    sede = models.CharField(max_length=10, choices=SEDE_CHOICES, default='AMBAS', verbose_name="Sede Asignada")
    modulo_defecto = models.CharField(max_length=20, choices=MODULO_CHOICES, default='ADMINISTRACION', verbose_name="Módulo Principal")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")

    def __str__(self):
        return f"Perfil de {self.user.username}"

    class Meta:
        db_table = 'perfil_usuario'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'

# Señales para crear/actualizar el perfil automáticamente al crear un usuario
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        # Usamos get_or_create para evitar el error si el Admin ya está gestionando la creación
        PerfilUsuario.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    # Solo intentamos guardar si el perfil ya existe
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
    else:
        # Si por alguna razón no existe (ej. usuarios viejos), lo creamos de forma segura
        PerfilUsuario.objects.get_or_create(user=instance)

class PrincipalDepartamento(models.Model):
    codigo_departamento = models.CharField(max_length=100, primary_key=True)
    nombre_departamento = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_departamento

    class Meta:
        verbose_name = "Departamento"
        db_table = 'principal_departamento'
        
class PrincipalMunicipio(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo_municipio = models.IntegerField()
    nombre_municipio = models.CharField(max_length=100)
    codigo_departamento = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre_municipio
    

    class Meta:
        managed = True
        db_table = 'principal_municipio'


# Modelo para la tabla: tipo_documento
class TipoDocumento(models.Model):
    # varchar2 [pk, not null, unique] se traduce a CharField con primary_key=True.
    # Necesita un max_length, por ejemplo 10 caracteres.
    id_documento = models.CharField(max_length=10, primary_key=True, verbose_name="ID Documento")

    # varchar2 se traduce a CharField.
    tipo_documento = models.CharField(max_length=100, verbose_name="Tipo de Documento")

    # integer se traduce a IntegerField.
    codigo_documento = models.IntegerField(verbose_name="Código Documento")

    class Meta:
        # Nombre de la tabla en la base de datos.
        db_table = 'tipo_documento'
        # Nombres para el panel de administración de Django.
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documento'

    def __str__(self):
        # Representación en texto del objeto (útil en el admin).
        return self.tipo_documento


# Modelo para la tabla: tipo_genero
class TipoGenero(models.Model):
    id_genero = models.CharField(max_length=10, primary_key=True, verbose_name="ID Género")
    genero = models.CharField(max_length=50, verbose_name="Género")
    codigo_genero = models.IntegerField(verbose_name="Código Género")

    class Meta:
        db_table = 'tipo_genero'
        verbose_name = 'Tipo de Género'
        verbose_name_plural = 'Tipos de Género'

    def __str__(self):
        return self.genero


# Modelo para la tabla: modalidades_de_consumo
# Nota: Corregí el nombre de la tabla de "modalides" a "modalidades".
class ModalidadesDeConsumo(models.Model):
    id_modalidades = models.CharField(max_length=10, primary_key=True, verbose_name="ID Modalidad")
    modalidad = models.CharField(max_length=150, verbose_name="Modalidad")
    cod_modalidad = models.CharField(max_length=20, verbose_name="Código de Modalidad")

    class Meta:
        db_table = 'modalidades_de_consumo'
        verbose_name = 'Modalidad de Consumo'
        verbose_name_plural = 'Modalidades de Consumo'

    def __str__(self):
        return self.modalidad


# Modelo para la tabla: nivel_grado_escolar
# Modelo para la tabla intermedia: municipio_modalidades
class MunicipioModalidades(models.Model):
    id = models.BigAutoField(primary_key=True)
    municipio = models.ForeignKey(
        PrincipalMunicipio,
        on_delete=models.CASCADE,
        verbose_name="Municipio",
        related_name="modalidades_configuradas"
    )
    modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.CASCADE,
        verbose_name="Modalidad",
        related_name="municipios_asignados"
    )

    class Meta:
        db_table = 'municipio_modalidades'
        verbose_name = 'Modalidad por Municipio'
        verbose_name_plural = 'Modalidades por Municipio'
        unique_together = [['municipio', 'modalidad']]
        ordering = ['municipio__nombre_municipio', 'modalidad__modalidad']

    def __str__(self):
        return f"{self.municipio.nombre_municipio} - {self.modalidad.modalidad}"


class NivelGradoEscolar(models.Model):
    id_grado_escolar = models.CharField(max_length=50, primary_key=True, verbose_name="ID Grado Escolar")
    grados_sedes = models.CharField(max_length=200, verbose_name="Grados Sedes")
    nivel_escolar_uapa = models.ForeignKey(
        'TablaGradosEscolaresUapa',
        on_delete=models.PROTECT,
        db_column='nivel_escolar_uapa',
        verbose_name="Nivel Escolar UAPA",
        related_name='niveles_grado'
    )

    class Meta:
        db_table = 'nivel_grado_escolar'
        verbose_name = 'Nivel Grado Escolar'
        verbose_name_plural = 'Niveles Grado Escolar'
        ordering = ['id_grado_escolar']

    def __str__(self):
        return f"{self.id_grado_escolar} - {self.nivel_escolar_uapa.nivel_escolar_uapa}"


class TablaGradosEscolaresUapa(models.Model):
    """
    Tabla para almacenar los grados escolares según UAPA.
    Solo contiene código y nivel escolar.
    """
    id_grado_escolar_uapa = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="Código Grado Escolar UAPA"
    )
    nivel_escolar_uapa = models.CharField(
        max_length=100,
        verbose_name="Nivel Escolar UAPA"
    )

    class Meta:
        db_table = 'tabla_grados_escolares_uapa'
        verbose_name = 'Grado Escolar UAPA'
        verbose_name_plural = 'Grados Escolares UAPA'
        ordering = ['id_grado_escolar_uapa']

    def __str__(self):
        return f"{self.id_grado_escolar_uapa} - {self.nivel_escolar_uapa}"


class RegistroActividad(models.Model):
    """
    Auditoría de acciones realizadas por los usuarios en cada módulo.
    Se registra automáticamente desde las vistas/servicios. Es de solo lectura.
    """

    MODULO_CHOICES = [
        ('facturacion', 'Facturación'),
        ('nutricion', 'Nutrición'),
        ('planeacion', 'Planeación'),
        ('principal', 'Datos Maestros'),
        ('dashboard', 'Dashboard'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuario"
    )
    modulo = models.CharField(max_length=50, choices=MODULO_CHOICES, verbose_name="Módulo")
    accion = models.CharField(max_length=100, verbose_name="Acción")
    descripcion = models.TextField(blank=True, verbose_name="Detalle")
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")
    exitoso = models.BooleanField(default=True, verbose_name="Exitoso")

    class Meta:
        db_table = 'principal_registro_actividad'
        verbose_name = 'Registro de Actividad'
        verbose_name_plural = 'Registros de Actividad'
        ordering = ['-fecha']

    def __str__(self):
        usuario = self.usuario.username if self.usuario else 'desconocido'
        return f"[{self.fecha:%Y-%m-%d %H:%M}] {usuario} — {self.modulo}/{self.accion}"

    @classmethod
    def registrar(cls, request, modulo, accion, descripcion='', exitoso=True):
        """
        Registra una acción de usuario. Silencia cualquier error para no
        interrumpir el flujo principal de la aplicación.
        """
        try:
            ip = (
                request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                or request.META.get('REMOTE_ADDR')
            ) or None
            cls.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                modulo=modulo,
                accion=accion,
                descripcion=descripcion,
                ip=ip,
                exitoso=exitoso,
            )
        except Exception as exc:
            logger.warning("No se pudo registrar actividad (%s/%s): %s", modulo, accion, exc)