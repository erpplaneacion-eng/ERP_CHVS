from django.db import models

class InformacionCodindem(models.Model):
    id_codindem = models.CharField(primary_key=True, max_length=50)
    id_departamento = models.IntegerField()
    departamento = models.CharField(max_length=100)
    id_municipio = models.IntegerField()
    municipio = models.CharField(max_length=100)
    id_tipo = models.IntegerField()
    tipo_comedor = models.CharField(max_length=50)
    dane = models.CharField(max_length=20)
    cod_interface = models.CharField(unique=True, max_length=20)
    institucion = models.CharField(max_length=255)
    sede = models.CharField(max_length=255)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    contacto = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'informacion_codindem'
            
    def __str__(self):
        # Esta es una representación mucho más descriptiva
        return f"{self.sede} - {self.municipio}"


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