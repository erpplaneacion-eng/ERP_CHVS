from django.db import models
from django.core.validators import MinValueValidator


class ListadosFocalizacion(models.Model):
    """
    Modelo para almacenar los listados de focalización procesados.
    Corresponde a la tabla facturacion_Listados_Focalizacion en la base de datos.
    """

    # Campos principales
    id_listados = models.CharField(
        max_length=50,
        primary_key=True,
        unique=True,
        verbose_name="ID Listados"
    )

    ano = models.IntegerField(
        validators=[MinValueValidator(2020)],
        verbose_name="Año"
    )

    etc = models.CharField(
        max_length=100,
        verbose_name="ETC (Entidad Territorial)"
    )

    institucion = models.CharField(
        max_length=200,
        verbose_name="Institución Educativa"
    )

    sede = models.CharField(
        max_length=200,
        verbose_name="Sede Educativa"
    )

    # Información del titular de derecho
    tipodoc = models.CharField(
        max_length=10,
        verbose_name="Tipo de Documento"
    )

    doc = models.CharField(
        max_length=50,
        verbose_name="Número de Documento"
    )

    apellido1 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Primer Apellido"
    )

    apellido2 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Segundo Apellido"
    )

    nombre1 = models.CharField(
        max_length=100,
        verbose_name="Primer Nombre"
    )

    nombre2 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Segundo Nombre"
    )

    fecha_nacimiento = models.CharField(
        max_length=20,
        verbose_name="Fecha de Nacimiento"
    )

    edad = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Edad"
    )

    etnia = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Etnia"
    )

    genero = models.CharField(
        max_length=10,
        verbose_name="Género"
    )

    grado_grupos = models.CharField(
        max_length=20,
        verbose_name="Grado y Grupos"
    )

    # Campos de complementos alimentarios
    complemento_alimentario_preparado_am = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Complemento Alimentario AM"
    )

    complemento_alimentario_preparado_pm = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Complemento Alimentario PM"
    )

    almuerzo_jornada_unica = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Almuerzo Jornada Única"
    )

    refuerzo_complemento_am_pm = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Refuerzo Complemento AM/PM"
    )

    focalizacion = models.CharField(
        max_length=10,
        verbose_name="Focalización"
    )

    programa = models.ForeignKey(
        'planeacion.Programa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='programa_id',
        verbose_name="Programa"
    )

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )

    class Meta:
        db_table = 'facturacion_listados_focalizacion'
        verbose_name = "Listado de Focalización"
        verbose_name_plural = "Listados de Focalización"
        ordering = ['-ano', 'etc', 'institucion', 'sede']
        indexes = [
            models.Index(fields=['ano', 'etc']),
            models.Index(fields=['focalizacion']),
            models.Index(fields=['sede']),
            models.Index(fields=['doc']),
            models.Index(fields=['fecha_creacion']),
        ]
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['doc', 'ano', 'focalizacion'],
        #         name='unique_doc_ano_focalizacion'
        #     )
        # ]

    def __str__(self):
        """Representación string del modelo."""
        return f"{self.nombre1} {self.apellido1} - {self.focalizacion} ({self.ano})"

    def get_nombre_completo(self):
        """Retorna el nombre completo del titular de derecho."""
        nombres = [self.nombre1, self.nombre2]
        apellidos = [self.apellido1, self.apellido2]

        nombre_completo = " ".join(filter(None, nombres))
        apellido_completo = " ".join(filter(None, apellidos))

        return f"{apellido_completo}, {nombre_completo}".strip(", ")

    def tiene_complemento_alimentario(self):
        """Verifica si tiene algún complemento alimentario asignado."""
        return any([
            self.complemento_alimentario_preparado_am,
            self.complemento_alimentario_preparado_pm,
            self.almuerzo_jornada_unica,
            self.refuerzo_complemento_am_pm
        ])

    @property
    def complementos_activos(self):
        """Retorna lista de complementos alimentarios activos."""
        complementos = []
        if self.complemento_alimentario_preparado_am:
            complementos.append("CAP AM")
        if self.complemento_alimentario_preparado_pm:
            complementos.append("CAP PM")
        if self.almuerzo_jornada_unica:
            complementos.append("Almuerzo JU")
        if self.refuerzo_complemento_am_pm:
            complementos.append("Refuerzo")
        return complementos