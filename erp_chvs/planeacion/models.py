from django.db import models
from principal.models import PrincipalMunicipio


class InstitucionesEducativas(models.Model):
    # Clave primaria - codigo_ie
    codigo_ie = models.CharField(primary_key=True, max_length=50, verbose_name="Código IE")

    # Nombre de la institución
    nombre_institucion = models.CharField(max_length=255, verbose_name="Nombre de la Institución")

    # Relación con municipio
    id_municipios = models.ForeignKey(
        PrincipalMunicipio,
        on_delete=models.PROTECT,
        verbose_name="Municipio",
        db_column="id_municipios"
    )

    class Meta:
        verbose_name = "Institución Educativa"
        verbose_name_plural = "Instituciones Educativas"
        db_table = 'instituciones_educativas'
        ordering = ['nombre_institucion']

    def __str__(self):
        return f"{self.nombre_institucion} - {self.id_municipios.nombre_municipio}"


class SedesEducativas(models.Model):
    # Clave primaria - cod_interprise
    cod_interprise = models.CharField(primary_key=True, max_length=50, verbose_name="Código Interprise")

    # Código DANE
    cod_dane = models.CharField(max_length=50, verbose_name="Código DANE")

    # Nombre de la sede educativa
    nombre_sede_educativa = models.CharField(max_length=255, verbose_name="Nombre Sede Educativa")

    # Zona (char)
    zona = models.CharField(max_length=1, verbose_name="Zona")

    # Dirección (puede ser nulo)
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")

    # Preparado
    preparado = models.CharField(max_length=50, verbose_name="Preparado")

    # Industrializado
    industrializado = models.CharField(max_length=50, verbose_name="Industrializado")

    # Relación con institución educativa (FK)
    codigo_ie = models.ForeignKey(
        InstitucionesEducativas,
        on_delete=models.PROTECT,
        verbose_name="Institución Educativa",
        db_column="codigo_ie"
    )

    class Meta:
        verbose_name = "Sede Educativa"
        verbose_name_plural = "Sedes Educativas"
        db_table = 'sedes_educativas'
        ordering = ['codigo_ie__nombre_institucion', 'nombre_sede_educativa']

    def __str__(self):
        return f"{self.nombre_sede_educativa} - {self.codigo_ie.nombre_institucion}"



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