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

    # Nombre genérico de la sede
    nombre_generico_sede = models.CharField(max_length=255, verbose_name="Nombre Genérico Sede", default="Sin especificar")

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

    # Campo para el contrato
    contrato = models.CharField(
        max_length=100,
        default='SIN_CONTRATO',  # Valor por defecto para registros existentes
        verbose_name="Contrato"
    )

    # Campo para el municipio - FK a PrincipalMunicipio
    municipio = models.ForeignKey(
        PrincipalMunicipio,
        on_delete=models.PROTECT,  # Protege de eliminación accidental
        verbose_name="Municipio",
        db_column="id_municipio"  # Nombre específico en BD
    )

    def get_nivel_escolar_uapa(self):
        """
        Determina el nivel escolar UAPA del programa basándose en los grados escolares
        de las planificaciones del municipio asociado.
        Retorna el nivel escolar más común o el primero encontrado.
        """
        from principal.models import TablaGradosEscolaresUapa
        from collections import Counter

        # Obtener planificaciones del municipio del programa
        planificaciones = PlanificacionRaciones.objects.filter(
            etc=self.municipio
        ).select_related('nivel_escolar__nivel_escolar_uapa')

        niveles_escolares = []
        for plan in planificaciones:
            if hasattr(plan, 'nivel_escolar') and plan.nivel_escolar and plan.nivel_escolar.nivel_escolar_uapa:
                niveles_escolares.append(plan.nivel_escolar.nivel_escolar_uapa)

        if not niveles_escolares:
            # Si no hay planificaciones, usar nivel por defecto (PRIMERA INFANCIA o el primero disponible)
            nivel_defecto = TablaGradosEscolaresUapa.objects.filter(
                id_grado_escolar_uapa='-1'
            ).first()
            if nivel_defecto:
                return nivel_defecto

            # Si no existe el nivel -1, retornar el primero disponible
            return TablaGradosEscolaresUapa.objects.first()

        # Retornar el nivel más común
        contador = Counter([nivel.id_grado_escolar_uapa for nivel in niveles_escolares])
        nivel_id_mas_comun = contador.most_common(1)[0][0]

        # Buscar el objeto completo
        for nivel in niveles_escolares:
            if nivel.id_grado_escolar_uapa == nivel_id_mas_comun:
                return nivel

        return None

    def __str__(self):
        return self.programa

    class Meta:
        verbose_name = "Programa"
        verbose_name_plural = "Programas"


class PlanificacionRaciones(models.Model):
    """
    Modelo para almacenar la planificación de raciones por sede educativa,
    focalización, nivel escolar y tipo de complemento alimentario.
    """
    # Relación con municipio (ETC)
    etc = models.ForeignKey(
        PrincipalMunicipio,
        on_delete=models.PROTECT,
        verbose_name="ETC (Municipio)",
        db_column="id_municipio"
    )

    # Focalización (F1, F2, F3, etc.)
    focalizacion = models.CharField(
        max_length=10,
        verbose_name="Focalización"
    )

    # Relación con sede educativa
    sede_educativa = models.ForeignKey(
        SedesEducativas,
        on_delete=models.PROTECT,
        verbose_name="Sede Educativa",
        db_column="cod_interprise"
    )

    # Nivel escolar (relación con tabla nivel_grado_escolar)
    from principal.models import NivelGradoEscolar
    nivel_escolar = models.ForeignKey(
        NivelGradoEscolar,
        on_delete=models.PROTECT,
        verbose_name="Nivel Escolar",
        db_column="id_nivel_grado"
    )

    # Año de planificación
    ano = models.IntegerField(
        verbose_name="Año",
        default=2025
    )

    # Cantidades editables por tipo de complemento alimentario
    cap_am = models.IntegerField(
        default=0,
        verbose_name="CAP AM (Complemento Alimentario Preparado AM)"
    )

    cap_pm = models.IntegerField(
        default=0,
        verbose_name="CAP PM (Complemento Alimentario Preparado PM)"
    )

    almuerzo_ju = models.IntegerField(
        default=0,
        verbose_name="Almuerzo Jornada Única"
    )

    refuerzo = models.IntegerField(
        default=0,
        verbose_name="Refuerzo Complemento AM/PM"
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
        db_table = 'planificacion_raciones'
        verbose_name = "Planificación de Raciones"
        verbose_name_plural = "Planificaciones de Raciones"
        ordering = ['etc__nombre_municipio', 'focalizacion', 'sede_educativa__nombre_sede_educativa']
        unique_together = [['etc', 'focalizacion', 'sede_educativa', 'nivel_escolar', 'ano']]
        indexes = [
            models.Index(fields=['etc', 'focalizacion', 'ano']),
            models.Index(fields=['sede_educativa']),
        ]

    def __str__(self):
        return f"{self.sede_educativa.nombre_sede_educativa} - {self.focalizacion} - {self.nivel_escolar.nivel_escolar_uapa} ({self.ano})"

    def total_raciones(self):
        """Retorna el total de raciones planificadas para este registro."""
        return self.cap_am + self.cap_pm + self.almuerzo_ju + self.refuerzo