from django.db import models
from planeacion.models import Programa, SedesEducativas

class TipoRuta(models.Model):
    # Ejemplo: 1=Víveres, 2=Congelados
    tipo = models.CharField(max_length=50, verbose_name="Tipo de Ruta")

    class Meta:
        db_table = 'logistica_tipos_rutas'
        verbose_name = "Tipo de Ruta"
        verbose_name_plural = "Tipos de Rutas"

    def __str__(self):
        return self.tipo

class Ruta(models.Model):
    nombre_ruta = models.CharField(max_length=100, verbose_name="Nombre de la Ruta") # Ej: "Ruta 4"
    id_tipo_ruta = models.ForeignKey(TipoRuta, on_delete=models.PROTECT, verbose_name="Tipo de Ruta")
    id_programa = models.ForeignKey(Programa, on_delete=models.CASCADE, verbose_name="Programa/Contrato") # Define si es Cali/Yumbo
    activa = models.BooleanField(default=True, verbose_name="Activa")
    
    class Meta:
        db_table = 'logistica_rutas'
        verbose_name = "Ruta"
        verbose_name_plural = "Rutas"
        unique_together = [['nombre_ruta', 'id_programa', 'id_tipo_ruta']]

    def __str__(self):
        return f"{self.nombre_ruta} ({self.id_tipo_ruta.tipo})"

class RutaSedes(models.Model):
    """Asocia múltiples sedes a un camión (ruta), y le da el orden del recorrido"""
    id_ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, verbose_name="Ruta")
    sede_educativa = models.ForeignKey(SedesEducativas, on_delete=models.CASCADE, verbose_name="Sede Educativa")
    orden_visita = models.PositiveIntegerField(default=1, verbose_name="Orden de visita", help_text="Ej: 1er colegio, 2do colegio...")

    class Meta:
        db_table = 'logistica_ruta_sedes'
        verbose_name = "Sede en Ruta"
        verbose_name_plural = "Sedes en Rutas"
        ordering = ['id_ruta', 'orden_visita']

    def __str__(self):
        return f"{self.id_ruta.nombre_ruta} -> {self.sede_educativa.nombre_sede_educativa} (#{self.orden_visita})"
