from django.db import models
from principal.models import ModalidadesDeConsumo
from planeacion.models import Programa


class PermisosNutricion(models.Model):
    """
    Modelo para gestionar permisos específicos del módulo de nutrición.
    """
    class Meta:
        verbose_name_plural = "Permisos de Nutrición"
        permissions = [
            ("view_contenido_nutricion", "Puede ver el contenido del módulo de nutrición"),
        ]


class TablaAlimentos2018Icbf(models.Model):
    """
    Tabla de composición nutricional de alimentos según ICBF 2018.
    Contiene información detallada de macronutrientes, micronutrientes y composición química.
    """
    codigo = models.CharField(primary_key=True, max_length=20, verbose_name="Código")
    nombre_del_alimento = models.CharField(max_length=200, verbose_name="Nombre del Alimento")
    parte_analizada = models.CharField(max_length=100, blank=True, null=True, verbose_name="Parte Analizada")
    humedad_g = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Humedad (g)")
    energia_kcal = models.IntegerField(verbose_name="Energía (kcal)")
    energia_kj = models.IntegerField(verbose_name="Energía (kJ)")
    proteina_g = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Proteína (g)")
    lipidos_g = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Lípidos (g)")
    carbohidratos_totales_g = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Carbohidratos Totales (g)")
    carbohidratos_disponibles_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Carbohidratos Disponibles (g)")
    fibra_dietaria_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Fibra Dietaria (g)")
    cenizas_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cenizas (g)")
    calcio_mg = models.IntegerField(blank=True, null=True, verbose_name="Calcio (mg)")
    hierro_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Hierro (mg)")
    sodio_mg = models.IntegerField(blank=True, null=True, verbose_name="Sodio (mg)")
    fosforo_mg = models.IntegerField(blank=True, null=True, verbose_name="Fósforo (mg)")
    yodo_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Yodo (mg)")
    zinc_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Zinc (mg)")
    magnesio_mg = models.IntegerField(blank=True, null=True, verbose_name="Magnesio (mg)")
    potasio_mg = models.IntegerField(blank=True, null=True, verbose_name="Potasio (mg)")
    tiamina_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Tiamina (mg)")
    riboflavina_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Riboflavina (mg)")
    niacina_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Niacina (mg)")
    folatos_mcg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Folatos (mcg)")
    vitamina_b12_mcg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Vitamina B12 (mcg)")
    vitamina_c_mg = models.IntegerField(blank=True, null=True, verbose_name="Vitamina C (mg)")
    vitamina_a_er = models.IntegerField(blank=True, null=True, verbose_name="Vitamina A (ER)")
    grasa_saturada_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Grasa Saturada (g)")
    grasa_monoinsaturada_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Grasa Monoinsaturada (g)")
    grasa_poliinsaturada_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Grasa Poliinsaturada (g)")
    colesterol_mg = models.IntegerField(blank=True, null=True, verbose_name="Colesterol (mg)")
    parte_comestible_field = models.IntegerField(db_column='parte_comestible_porcentaje', blank=True, null=True, verbose_name="Parte Comestible (%)")

    class Meta:
        managed = True
        db_table = 'TABLA_ALIMENTOS_2018_ICBF'
        verbose_name = 'Alimento ICBF 2018'
        verbose_name_plural = 'Alimentos ICBF 2018'
        ordering = ['nombre_del_alimento']

    def __str__(self):
        return self.nombre_del_alimento


class TablaMenus(models.Model):
    """
    Modelo para gestionar menús del programa de alimentación.
    Relaciona programas (contratos) con modalidades de consumo y menús específicos.
    """
    id_menu = models.AutoField(
        primary_key=True,
        verbose_name="ID del Menú"
    )
    menu = models.CharField(
        max_length=255,
        verbose_name="Nombre del Menú"
    )
    id_modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.PROTECT,
        db_column='id_modalidad',
        verbose_name="Modalidad de Consumo",
        related_name='menus'
    )
    id_contrato = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        db_column='id_contrato',
        verbose_name="Programa/Contrato",
        related_name='menus'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )

    def __str__(self):
        return f"{self.menu} - {self.id_modalidad.modalidad}"

    class Meta:
        db_table = 'tabla_menus'
        verbose_name = "Menú"
        verbose_name_plural = "Menús"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['id_modalidad']),
            models.Index(fields=['id_contrato']),
        ]


class TablaPreparaciones(models.Model):
    """
    Modelo para gestionar preparaciones/recetas asociadas a un menú.
    Cada preparación pertenece a un menú específico.
    """
    id_preparacion = models.AutoField(
        primary_key=True,
        verbose_name="ID de la Preparación"
    )
    preparacion = models.CharField(
        max_length=255,
        verbose_name="Nombre de la Preparación"
    )
    id_menu = models.ForeignKey(
        TablaMenus,
        on_delete=models.CASCADE,
        db_column='id_menu',
        verbose_name="Menú",
        related_name='preparaciones'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    def __str__(self):
        return f"{self.preparacion} ({self.id_menu.menu})"

    class Meta:
        db_table = 'tabla_preparaciones'
        verbose_name = "Preparación/Receta"
        verbose_name_plural = "Preparaciones/Recetas"
        ordering = ['preparacion']


class TablaIngredientesSiesa(models.Model):
    """
    Modelo para gestionar ingredientes del inventario Siesa.
    Representa los ingredientes disponibles en el sistema de inventario.
    """
    id_ingrediente_siesa = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="Código del Ingrediente"
    )
    nombre_ingrediente = models.CharField(
        max_length=255,
        verbose_name="Nombre del Ingrediente"
    )

    def __str__(self):
        return f"{self.id_ingrediente_siesa} - {self.nombre_ingrediente}"

    class Meta:
        db_table = 'tabla_ingredientes_siesa'
        verbose_name = "Ingrediente de Inventario"
        verbose_name_plural = "Ingredientes de Inventario"
        ordering = ['nombre_ingrediente']


class TablaPreparacionIngredientes(models.Model):
    """
    Modelo para la relación muchos-a-muchos entre preparaciones e ingredientes.
    Registra qué ingredientes lleva cada preparación.
    """
    id_preparacion = models.ForeignKey(
        TablaPreparaciones,
        on_delete=models.CASCADE,
        db_column='id_preparacion',
        verbose_name="Preparación",
        related_name='ingredientes'
    )
    id_ingrediente_siesa = models.ForeignKey(
        TablaIngredientesSiesa,
        on_delete=models.CASCADE,
        db_column='id_ingrediente_siesa',
        verbose_name="Ingrediente",
        related_name='preparaciones'
    )

    def __str__(self):
        return f"{self.id_preparacion.preparacion} - {self.id_ingrediente_siesa.nombre_ingrediente}"

    class Meta:
        db_table = 'tabla_preparacion_ingredientes'
        unique_together = ('id_preparacion', 'id_ingrediente_siesa')
        verbose_name = "Ingrediente de Preparación"
        verbose_name_plural = "Ingredientes de Preparaciones"
        ordering = ['id_preparacion__preparacion', 'id_ingrediente_siesa__nombre_ingrediente']
        indexes = [
            models.Index(fields=['id_preparacion']),
            models.Index(fields=['id_ingrediente_siesa']),
        ]