from django.db import models
from principal.models import PrincipalDepartamento, PrincipalMunicipio


class InstitucionesEducativas(models.Model):
    # Clave primaria
    codigo_dane = models.CharField(primary_key=True, max_length=20, verbose_name="Código DANE")

    # Información básica de la institución
    nombre_institucion = models.CharField(max_length=255, verbose_name="Nombre de la Institución")

    # Relaciones con ubicación geográfica
    departamento = models.ForeignKey(
        PrincipalDepartamento,
        on_delete=models.PROTECT,
        verbose_name="Departamento"
    )
    municipio = models.ForeignKey(
        PrincipalMunicipio,
        on_delete=models.PROTECT,
        verbose_name="Municipio"
    )

    # Información de contacto
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")

    # Información administrativa
    sector = models.CharField(
        max_length=20,
        choices=[
            ('OFICIAL', 'Oficial'),
            ('PRIVADO', 'Privado'),
            ('MIXTO', 'Mixto'),
        ],
        default='OFICIAL',
        verbose_name="Sector"
    )

    # Información de contacto institucional
    rector = models.CharField(max_length=255, blank=True, null=True, verbose_name="Rector/Director")

    # Estado de la institución
    estado = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVO', 'Activo'),
            ('INACTIVO', 'Inactivo'),
            ('SUSPENDIDO', 'Suspendido'),
        ],
        default='ACTIVO',
        verbose_name="Estado"
    )

    # Fechas de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        verbose_name = "Institución Educativa"
        verbose_name_plural = "Instituciones Educativas"
        db_table = 'instituciones_educativas'
        ordering = ['nombre_institucion']

    def __str__(self):
        return f"{self.nombre_institucion} - {self.municipio.nombre_municipio}"


class SedesEducativas(models.Model):
    # Clave primaria
    codigo_sede = models.CharField(primary_key=True, max_length=20, verbose_name="Código de Sede")

    # Relación con institución educativa
    institucion = models.ForeignKey(
        InstitucionesEducativas,
        on_delete=models.CASCADE,
        related_name='sedes',
        verbose_name="Institución Educativa"
    )

    # Información básica de la sede
    nombre_sede = models.CharField(max_length=255, verbose_name="Nombre de la Sede")

    # Información de ubicación específica
    direccion = models.TextField(verbose_name="Dirección de la Sede")
    zona = models.CharField(
        max_length=10,
        choices=[
            ('URBANA', 'Urbana'),
            ('RURAL', 'Rural'),
        ],
        verbose_name="Zona"
    )

    # Información de contacto de la sede
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name="Teléfono")
    coordinador = models.CharField(max_length=255, blank=True, null=True, verbose_name="Coordinador")

    # Información del comedor/alimentación
    tiene_comedor = models.BooleanField(default=False, verbose_name="Tiene Comedor")
    tipo_atencion = models.CharField(
        max_length=50,
        choices=[
            ('DESAYUNO', 'Desayuno'),
            ('ALMUERZO', 'Almuerzo'),
            ('REFRIGERIO_AM', 'Refrigerio AM'),
            ('REFRIGERIO_PM', 'Refrigerio PM'),
            ('COMPLEMENTO', 'Complemento Alimentario'),
            ('MULTIPLE', 'Múltiples Atenciones'),
        ],
        blank=True,
        null=True,
        verbose_name="Tipo de Atención Alimentaria"
    )

    # Capacidad y información operativa
    capacidad_beneficiarios = models.IntegerField(blank=True, null=True, verbose_name="Capacidad de Beneficiarios")

    # Jornadas disponibles
    jornada_manana = models.BooleanField(default=False, verbose_name="Jornada Mañana")
    jornada_tarde = models.BooleanField(default=False, verbose_name="Jornada Tarde")
    jornada_nocturna = models.BooleanField(default=False, verbose_name="Jornada Nocturna")
    jornada_unica = models.BooleanField(default=False, verbose_name="Jornada Única")

    # Estado de la sede
    estado = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVO', 'Activo'),
            ('INACTIVO', 'Inactivo'),
            ('MANTENIMIENTO', 'En Mantenimiento'),
        ],
        default='ACTIVO',
        verbose_name="Estado"
    )

    # Fechas de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        verbose_name = "Sede Educativa"
        verbose_name_plural = "Sedes Educativas"
        db_table = 'sedes_educativas'
        ordering = ['institucion__nombre_institucion', 'nombre_sede']

    def __str__(self):
        return f"{self.nombre_sede} - {self.institucion.nombre_institucion}"



class Programa(models.Model):
    # Django crea automáticamente un campo 'id' numérico y autoincremental como clave primaria.
    # No necesitas definir 'id_programa' a menos que quieras un comportamiento diferente.
    
    # Campo para el nombre del programa (texto corto)
    programa = models.CharField(max_length=200, verbose_name="Nombre del Programa")

    # Campos de fecha
    fecha_inicial = models.DateField(verbose_name="Fecha Inicial")
    fecha_final = models.DateField(verbose_name="Fecha Final")

    # Opciones para el campo de estado
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    # Campo de estado con opciones predefinidas
    estado = models.CharField(
        max_length=8,
        choices=ESTADO_CHOICES,
        default='activo',  # Valor por defecto al crear un nuevo programa
        verbose_name="Estado"
    )

    # Campo para la imagen. Los archivos se guardarán en 'media/programas_imagenes/'
    imagen = models.ImageField(
        upload_to='programas_imagenes/',
        blank=True,  # Permite que el campo esté vacío en el formulario
        null=True,   # Permite que el valor en la base de datos sea NULL
        verbose_name="Imagen del Programa"
    )
    
    def __str__(self):
        return self.programa

    class Meta:
        verbose_name = "Programa"
        verbose_name_plural = "Programas"