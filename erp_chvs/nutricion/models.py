from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from principal.models import ModalidadesDeConsumo, TablaGradosEscolaresUapa
from planeacion.models import Programa


class GruposAlimentos(models.Model):
    """
    Catálogo de grupos de alimentos según la clasificación nutricional.
    Ej: Cereales, Frutas, Lácteos, etc.
    """
    id_grupo_alimentos = models.CharField(
        primary_key=True, 
        max_length=10,
        verbose_name="ID Grupo Alimentos"
    )
    grupo_alimentos = models.CharField(
        max_length=100,
        verbose_name="Grupo de Alimentos"
    )

    def __str__(self):
        return self.grupo_alimentos

    class Meta:
        db_table = 'nutricion_grupos_alimento'
        verbose_name = "Grupo de Alimento"
        verbose_name_plural = "Grupos de Alimentos"
        ordering = ['id_grupo_alimentos']


class ComponentesAlimentos(models.Model):
    """
    Catálogo de componentes o tipos de platos que conforman un menú.
    Ej: Bebida con leche, Alimento proteico, Cereal acompañante, etc.
    """
    id_componente = models.CharField(
        primary_key=True, 
        max_length=10,
        verbose_name="ID Componente"
    )
    componente = models.CharField(
        max_length=100,
        verbose_name="Componente"
    )
    id_grupo_alimentos = models.ForeignKey(
        GruposAlimentos, 
        on_delete=models.PROTECT,
        db_column='id_grupo_alimentos',
        verbose_name="Grupo de Alimentos",
        related_name='componentes'
    )

    def __str__(self):
        return self.componente

    class Meta:
        db_table = 'nutricion_componentes_alimentos'
        verbose_name = "Componente de Alimento"
        verbose_name_plural = "Componentes de Alimentos"
        ordering = ['componente']


class ComponentesModalidades(models.Model):
    """
    Tabla puente para asociar componentes de alimentos con modalidades de consumo.
    Permite relación muchos-a-muchos sin duplicados.
    """
    id_componente = models.ForeignKey(
        ComponentesAlimentos,
        on_delete=models.CASCADE,
        db_column='id_componente',
        related_name='componentes_modalidades',
        verbose_name="Componente de Alimento"
    )
    id_modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.CASCADE,
        db_column='id_modalidades',
        related_name='componentes_modalidades',
        verbose_name="Modalidad de Consumo"
    )

    class Meta:
        db_table = 'nutricion_componentes_modalidades'
        verbose_name = "Componente por Modalidad"
        verbose_name_plural = "Componentes por Modalidad"
        unique_together = [['id_componente', 'id_modalidad']]
        ordering = ['id_componente', 'id_modalidad']
        indexes = [
            models.Index(fields=['id_componente']),
            models.Index(fields=['id_modalidad']),
        ]

    def __str__(self):
        return f"{self.id_componente.componente} - {self.id_modalidad.modalidad}"


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
    energia_kcal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Energía (kcal)")
    energia_kj = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Energía (kJ)")
    proteina_g = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Proteína (g)")
    lipidos_g = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Lípidos (g)")
    carbohidratos_totales_g = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Carbohidratos Totales (g)")
    carbohidratos_disponibles_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Carbohidratos Disponibles (g)")
    fibra_dietaria_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Fibra Dietaria (g)")
    cenizas_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cenizas (g)")
    calcio_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Calcio (mg)")
    hierro_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Hierro (mg)")
    sodio_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Sodio (mg)")
    fosforo_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Fósforo (mg)")
    yodo_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Yodo (mg)")
    zinc_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Zinc (mg)")
    magnesio_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Magnesio (mg)")
    potasio_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Potasio (mg)")
    tiamina_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Tiamina (mg)")
    riboflavina_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Riboflavina (mg)")
    niacina_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Niacina (mg)")
    folatos_mcg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Folatos (mcg)")
    vitamina_b12_mcg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Vitamina B12 (mcg)")
    vitamina_c_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Vitamina C (mg)")
    vitamina_a_er = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Vitamina A (ER)")
    grasa_saturada_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Grasa Saturada (g)")
    grasa_monoinsaturada_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Grasa Monoinsaturada (g)")
    grasa_poliinsaturada_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Grasa Poliinsaturada (g)")
    colesterol_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Colesterol (mg)")
    parte_comestible_field = models.DecimalField(max_digits=5, decimal_places=2, db_column='parte_comestible_porcentaje', blank=True, null=True, verbose_name="Parte Comestible (%)")
    id_componente = models.ForeignKey(
        ComponentesAlimentos,
        on_delete=models.PROTECT,
        db_column='id_componente',
        verbose_name="Componente de Alimento",
        related_name='alimentos_icbf',
        null=True,
        blank=True
    )

    class Meta:
        managed = True
        db_table = 'nutricion_tabla_alimentos_2018_icb'
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
    semana = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        verbose_name="Semana del Ciclo",
        help_text="Semana 1-4, calculada automáticamente para menús 1-20"
    )

    def __str__(self):
        return f"{self.menu} - {self.id_modalidad.modalidad}"

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para auto-calcular la semana
        basándose en el número de menú (1-20).

        Menús 1-5: Semana 1
        Menús 6-10: Semana 2
        Menús 11-15: Semana 3
        Menús 16-20: Semana 4
        Menús especiales (no numéricos): Semana None
        """
        if self.menu:
            try:
                num = int(self.menu)
                if 1 <= num <= 20:
                    # Fórmula: ((num - 1) // 5) + 1
                    # Ejemplos: 1-5 → 1, 6-10 → 2, 11-15 → 3, 16-20 → 4
                    self.semana = ((num - 1) // 5) + 1
                else:
                    self.semana = None  # Menús fuera del rango 1-20
            except (ValueError, TypeError):
                self.semana = None  # Menús especiales (texto no numérico)

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'nutricion_tabla_menus'
        verbose_name = "Menú"
        verbose_name_plural = "Menús"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['id_modalidad']),
            models.Index(fields=['id_contrato']),
        ]


class FirmaNutricionalContrato(models.Model):
    """
    Configuración de firmas nutricionales por contrato/programa.
    Mantiene un único registro vigente por programa.
    """
    programa = models.OneToOneField(
        Programa,
        on_delete=models.CASCADE,
        db_column='id_contrato',
        related_name='firma_nutricional',
        verbose_name="Contrato/Programa"
    )

    # Profesional que elabora el análisis
    elabora_nombre = models.CharField(max_length=255, verbose_name="Nombre Dietista (Elabora)")
    elabora_matricula = models.CharField(max_length=50, verbose_name="Matrícula Profesional (Elabora)")
    elabora_firma_texto = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Firma Texto (Elabora)"
    )
    elabora_firma_imagen = models.ImageField(
        upload_to='firmas_nutricion/',
        blank=True,
        null=True,
        verbose_name="Firma Imagen (Elabora)"
    )

    # Profesional que aprueba el análisis
    aprueba_nombre = models.CharField(max_length=255, verbose_name="Nombre Dietista (Aprueba)")
    aprueba_matricula = models.CharField(max_length=50, verbose_name="Matrícula Profesional (Aprueba)")
    aprueba_firma_texto = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Firma Texto (Aprueba)"
    )
    aprueba_firma_imagen = models.ImageField(
        upload_to='firmas_nutricion/',
        blank=True,
        null=True,
        verbose_name="Firma Imagen (Aprueba)"
    )

    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha Actualización")
    usuario_modificacion = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Usuario que Modificó"
    )

    class Meta:
        db_table = 'nutricion_firma_nutricional_contrato'
        verbose_name = "Firma Nutricional por Contrato"
        verbose_name_plural = "Firmas Nutricionales por Contrato"
        ordering = ['programa__programa']

    def __str__(self):
        return f"Firmas nutricionales - {self.programa.programa}"

    @staticmethod
    def _normalizar_campo_texto(value):
        if not value:
            return value
        return str(value).strip().upper()

    @staticmethod
    def _optimizar_firma(imagen_field):
        """
        Optimiza la firma para reducir peso y remover fondo claro.
        """
        if not imagen_field or not hasattr(imagen_field, 'file'):
            return imagen_field

        try:
            import os
            import sys
            from io import BytesIO
            from PIL import Image
            from django.core.files.uploadedfile import InMemoryUploadedFile

            img = Image.open(imagen_field).convert('RGBA')

            # Transparencia para fondo claro.
            pixels = img.getdata()
            cleaned = []
            for r, g, b, a in pixels:
                if r > 240 and g > 240 and b > 240:
                    cleaned.append((255, 255, 255, 0))
                else:
                    cleaned.append((r, g, b, 255))
            img.putdata(cleaned)

            # Recortar bordes transparentes.
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)

            # Reducir tamaño para Excel.
            max_width = 500
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_height = max(1, int(img.height * ratio))
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            output = BytesIO()
            img.save(output, format='PNG', optimize=True)
            output.seek(0)

            original_name = os.path.basename(imagen_field.name)
            base_name, _ = os.path.splitext(original_name)
            file_name = f"{base_name}.png"

            return InMemoryUploadedFile(
                output,
                'ImageField',
                file_name,
                'image/png',
                sys.getsizeof(output),
                None
            )
        except Exception:
            return imagen_field

    def save(self, *args, **kwargs):
        self.elabora_nombre = self._normalizar_campo_texto(self.elabora_nombre)
        self.elabora_matricula = self._normalizar_campo_texto(self.elabora_matricula)
        self.elabora_firma_texto = self._normalizar_campo_texto(self.elabora_firma_texto)
        self.aprueba_nombre = self._normalizar_campo_texto(self.aprueba_nombre)
        self.aprueba_matricula = self._normalizar_campo_texto(self.aprueba_matricula)
        self.aprueba_firma_texto = self._normalizar_campo_texto(self.aprueba_firma_texto)

        if self.elabora_firma_imagen:
            self.elabora_firma_imagen = self._optimizar_firma(self.elabora_firma_imagen)
        if self.aprueba_firma_imagen:
            self.aprueba_firma_imagen = self._optimizar_firma(self.aprueba_firma_imagen)

        super().save(*args, **kwargs)


class TablaPreparaciones(models.Model):
    """
    Modelo para gestionar preparaciones/recetas asociadas a un menú.
    Cada preparación pertenece a un menú específico y a un componente de alimento.
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
    id_componente = models.ForeignKey(
        ComponentesAlimentos,
        on_delete=models.PROTECT,
        db_column='id_componente',
        verbose_name="Componente de Alimento",
        related_name='preparaciones',
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    def __str__(self):
        return f"{self.preparacion} ({self.id_menu.menu})"

    class Meta:
        db_table = 'nutricion_tabla_preparaciones'
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
        TablaAlimentos2018Icbf,
        on_delete=models.CASCADE,
        db_column='id_ingrediente_siesa',
        verbose_name="Ingrediente (ICBF 2018)",
        related_name='preparaciones'
    )
    gramaje = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Gramaje (g)"
    )

    def __str__(self):
        return f"{self.id_preparacion.preparacion} - {self.id_ingrediente_siesa.nombre_del_alimento}"

    class Meta:
        db_table = 'nutricion_tabla_preparacion_ingredientes'
        unique_together = ('id_preparacion', 'id_ingrediente_siesa')
        verbose_name = "Ingrediente de Preparación"
        verbose_name_plural = "Ingredientes de Preparaciones"
        ordering = ['id_preparacion__preparacion', 'id_ingrediente_siesa__nombre_del_alimento']
        indexes = [
            models.Index(fields=['id_preparacion']),
            models.Index(fields=['id_ingrediente_siesa']),
        ]


class TablaRequerimientosNutricionales(models.Model):
    """
    Tabla de requerimientos nutricionales por nivel escolar y modalidad de consumo.
    Define los límites máximos de macronutrientes y micronutrientes que se deben suministrar.

    CAMBIO IMPORTANTE (Febrero 2025):
    - Ahora considera NIVEL ESCOLAR + MODALIDAD DE CONSUMO
    - Cada modalidad (CAJM/JT, Almuerzo, etc.) tiene requerimientos específicos
    - Los requerimientos se basan en la Minuta Patrón ICBF (Resolución UAPA)

    Los requerimientos representan el 100% de adecuación nutricional permitido para esa modalidad.
    Los rangos de evaluación son:
    - 0-35%: Óptimo (verde) - Aporte bajo pero seguro
    - 35.1-70%: Aceptable (amarillo) - Aporte moderado
    - >70%: Alto (rojo) - Aporte elevado, cerca del límite máximo

    Ejemplo:
    - CAJM/JT Preescolar: 276 Kcal (20% del requerimiento diario de 1300 Kcal)
    - Almuerzo Preescolar: 417 Kcal (32% del requerimiento diario de 1300 Kcal)
    """
    id_requerimiento_nutricional = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="ID Requerimiento"
    )
    calorias_kcal = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        verbose_name="Calorías (Kcal)"
    )
    proteina_g = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        verbose_name="Proteína (g)"
    )
    grasa_g = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        verbose_name="Grasa (g)"
    )
    cho_g = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        verbose_name="CHO (g)"
    )
    calcio_mg = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        verbose_name="Calcio (mg)"
    )
    hierro_mg = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        verbose_name="Hierro (mg)"
    )
    sodio_mg = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        verbose_name="Sodio (mg)"
    )
    id_nivel_escolar_uapa = models.ForeignKey(
        'principal.TablaGradosEscolaresUapa',
        on_delete=models.PROTECT,
        db_column='id_nivel_escolar_uapa',
        verbose_name="Nivel Escolar UAPA",
        related_name='requerimientos_nutricionales'
    )
    id_modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.PROTECT,
        db_column='id_modalidad',
        verbose_name="Modalidad de Consumo",
        related_name='requerimientos_nutricionales',
        null=True,  # Permitir NULL para compatibilidad con datos existentes
        blank=True
    )

    class Meta:
        db_table = 'nutricion_total_aporte_promedio_diario'
        verbose_name = 'Requerimiento Nutricional'
        verbose_name_plural = 'Requerimientos Nutricionales'
        ordering = ['id_nivel_escolar_uapa', 'id_modalidad']
        # Ahora la combinación única es nivel + modalidad
        unique_together = [['id_nivel_escolar_uapa', 'id_modalidad']]

    def __str__(self):
        modalidad_str = f" - {self.id_modalidad.modalidad}" if self.id_modalidad else ""
        return f"{self.id_nivel_escolar_uapa.nivel_escolar_uapa}{modalidad_str} - {self.calorias_kcal} Kcal"


class AdecuacionTotalPorcentaje(models.Model):
    """
    Tabla de adecuación total en porcentaje por nivel escolar y modalidad de consumo.
    Almacena los porcentajes de adecuación nutricional calculados comparando
    los valores reales del menú contra los requerimientos nutricionales.

    Los valores en esta tabla representan el % de cumplimiento de cada nutriente:
    - 0-35%: Óptimo (verde) - Aporte bajo pero seguro
    - 35.1-70%: Aceptable (amarillo) - Aporte moderado
    - >70%: Alto (rojo) - Aporte elevado, cerca del límite máximo (100%)

    Relación con otras tablas:
    - Se calcula a partir de: TablaAnalisisNutricionalMenu (valores reales)
    - Se compara contra: TablaRequerimientosNutricionales (valores límite 100%)
    """
    id_adecuacion_porcentaje = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="ID Adecuación Porcentaje"
    )
    calorias_porc = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Calorías (%)"
    )
    proteina_porc = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Proteína (%)"
    )
    grasa_porc = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Grasa (%)"
    )
    cho_porc = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="CHO (%)"
    )
    calcio_porc = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Calcio (%)"
    )
    hierro_porc = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Hierro (%)"
    )
    sodio_porc = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Sodio (%)"
    )
    id_nivel_escolar_uapa = models.ForeignKey(
        'principal.TablaGradosEscolaresUapa',
        on_delete=models.PROTECT,
        db_column='id_nivel_escolar_uapa',
        verbose_name="Nivel Escolar UAPA",
        related_name='adecuaciones_porcentaje'
    )
    id_modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.PROTECT,
        db_column='id_modalidad',
        verbose_name="Modalidad de Consumo",
        related_name='adecuaciones_porcentaje',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'nutricion_adecuacion_total_porc'
        verbose_name = 'Adecuación Total Porcentaje'
        verbose_name_plural = 'Adecuaciones Totales Porcentaje'
        ordering = ['id_nivel_escolar_uapa', 'id_modalidad']
        unique_together = [['id_nivel_escolar_uapa', 'id_modalidad']]

    def __str__(self):
        modalidad_str = f" - {self.id_modalidad.modalidad}" if self.id_modalidad else ""
        return f"{self.id_nivel_escolar_uapa.nivel_escolar_uapa}{modalidad_str} - {self.calorias_porc}%"


class TablaAnalisisNutricionalMenu(models.Model):
    """
    Tabla para guardar los análisis nutricionales de menús por nivel escolar.
    Almacena los pesos configurados y valores calculados para cada nivel.

    Esta tabla permite:
    - Guardar configuraciones de pesos para cada nivel escolar
    - Restaurar análisis previos
    - Hacer seguimiento histórico de cambios
    - Comparar diferentes configuraciones
    """
    id_analisis = models.AutoField(
        primary_key=True,
        verbose_name="ID Análisis"
    )
    id_menu = models.ForeignKey(
        TablaMenus,
        on_delete=models.CASCADE,
        db_column='id_menu',
        verbose_name="Menú",
        related_name='analisis_nutricionales'
    )
    id_nivel_escolar_uapa = models.ForeignKey(
        'principal.TablaGradosEscolaresUapa',
        on_delete=models.PROTECT,
        db_column='id_nivel_escolar_uapa',
        verbose_name="Nivel Escolar UAPA",
        related_name='analisis_nutricionales'
    )

    # ========== TOTALES CALCULADOS ==========
    total_calorias = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Calorías (kcal)"
    )
    total_proteina = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Proteína (g)"
    )
    total_grasa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Grasa (g)"
    )
    total_cho = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total CHO (g)"
    )
    total_calcio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Calcio (mg)"
    )
    total_hierro = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Hierro (mg)"
    )
    total_sodio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Sodio (mg)"
    )
    total_peso_neto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Peso Neto (g)"
    )
    total_peso_bruto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Peso Bruto (g)"
    )

    # ========== PORCENTAJES DE ADECUACIÓN ==========
    porcentaje_calorias = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Adecuación Calorías"
    )
    porcentaje_proteina = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Adecuación Proteína"
    )
    porcentaje_grasa = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Adecuación Grasa"
    )
    porcentaje_cho = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Adecuación CHO"
    )
    porcentaje_calcio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Adecuación Calcio"
    )
    porcentaje_hierro = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Adecuación Hierro"
    )
    porcentaje_sodio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Adecuación Sodio"
    )

    # ========== ESTADOS DE ADECUACIÓN ==========
    # Valores: 'optimo', 'aceptable', 'alto'
    estado_calorias = models.CharField(
        max_length=20,
        default='optimo',
        verbose_name="Estado Calorías"
    )
    estado_proteina = models.CharField(
        max_length=20,
        default='optimo',
        verbose_name="Estado Proteína"
    )
    estado_grasa = models.CharField(
        max_length=20,
        default='optimo',
        verbose_name="Estado Grasa"
    )
    estado_cho = models.CharField(
        max_length=20,
        default='optimo',
        verbose_name="Estado CHO"
    )
    estado_calcio = models.CharField(
        max_length=20,
        default='optimo',
        verbose_name="Estado Calcio"
    )
    estado_hierro = models.CharField(
        max_length=20,
        default='optimo',
        verbose_name="Estado Hierro"
    )
    estado_sodio = models.CharField(
        max_length=20,
        default='optimo',
        verbose_name="Estado Sodio"
    )

    # ========== METADATOS ==========
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )
    usuario_modificacion = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Usuario que Modificó"
    )
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas u Observaciones"
    )

    class Meta:
        db_table = 'nutricion_tabla_analisis_nutricional_menu'
        verbose_name = 'Análisis Nutricional de Menú'
        verbose_name_plural = 'Análisis Nutricionales de Menús'
        ordering = ['-fecha_actualizacion']
        unique_together = [['id_menu', 'id_nivel_escolar_uapa']]
        indexes = [
            models.Index(fields=['id_menu']),
            models.Index(fields=['id_nivel_escolar_uapa']),
            models.Index(fields=['fecha_actualizacion']),
        ]

    def __str__(self):
        return f"Análisis {self.id_menu.menu} - {self.id_nivel_escolar_uapa.nivel_escolar_uapa}"


class TablaIngredientesPorNivel(models.Model):
    """
    Tabla para guardar los pesos configurados de cada ingrediente por nivel escolar.

    Esta tabla almacena:
    - Peso neto y bruto de cada ingrediente
    - Valores nutricionales calculados para ese peso
    - Relación con el análisis nutricional del menú

    Permite restaurar configuraciones exactas y hacer seguimiento de cambios.
    """
    id_ingrediente_nivel = models.AutoField(
        primary_key=True,
        verbose_name="ID Ingrediente Nivel"
    )
    id_analisis = models.ForeignKey(
        TablaAnalisisNutricionalMenu,
        on_delete=models.CASCADE,
        db_column='id_analisis',
        verbose_name="Análisis Nutricional",
        related_name='ingredientes_configurados'
    )
    id_preparacion = models.ForeignKey(
        TablaPreparaciones,
        on_delete=models.CASCADE,
        db_column='id_preparacion',
        verbose_name="Preparación",
        related_name='ingredientes_por_nivel'
    )
    id_ingrediente_siesa = models.ForeignKey(
        TablaIngredientesSiesa,
        on_delete=models.SET_NULL,
        db_column='id_ingrediente_siesa',
        verbose_name="Ingrediente Siesa",
        related_name='configuraciones_por_nivel',
        null=True,
        blank=True
    )

    # ========== PESOS CONFIGURADOS ==========
    peso_neto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100,
        verbose_name="Peso Neto (g)"
    )
    peso_bruto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100,
        verbose_name="Peso Bruto (g)"
    )
    parte_comestible = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        verbose_name="% Parte Comestible"
    )

    # ========== VALORES NUTRICIONALES CALCULADOS ==========
    # Para este peso específico
    calorias = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Calorías (kcal)"
    )
    proteina = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Proteína (g)"
    )
    grasa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Grasa (g)"
    )
    cho = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="CHO (g)"
    )
    calcio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Calcio (mg)"
    )
    hierro = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Hierro (mg)"
    )
    sodio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Sodio (mg)"
    )

    # ========== REFERENCIA AL ALIMENTO ICBF ==========
    codigo_icbf = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Código ICBF"
    )

    class Meta:
        db_table = 'nutricion_tabla_ingredientes_por_nivel'
        verbose_name = 'Ingrediente Configurado por Nivel'
        verbose_name_plural = 'Ingredientes Configurados por Nivel'
        ordering = ['id_preparacion', 'codigo_icbf']
        unique_together = [['id_analisis', 'id_preparacion', 'codigo_icbf']]
        indexes = [
            models.Index(fields=['id_analisis']),
            models.Index(fields=['id_preparacion']),
        ]

    def __str__(self):
        return f"{self.codigo_icbf or 'sin_codigo'} - {self.peso_neto}g"


class RequerimientoSemanal(models.Model):
    """
    Modelo para gestionar los requerimientos semanales de grupos de alimentos por modalidad.
    Define la frecuencia mínima semanal que debe cumplir cada grupo de alimento
    según la modalidad de consumo.

    Ejemplo: Para modalidad "Almuerzo", el grupo "Lácteos" debe aparecer
    mínimo 3 veces por semana.
    """
    id = models.AutoField(
        primary_key=True,
        verbose_name="ID"
    )
    modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.PROTECT,
        verbose_name="Modalidad de Consumo",
        related_name='requerimientos_semanales'
    )
    grupo = models.ForeignKey(
        GruposAlimentos,
        on_delete=models.PROTECT,
        verbose_name="Grupo de Alimentos",
        related_name='requerimientos_semanales'
    )
    frecuencia = models.IntegerField(
        verbose_name="Frecuencia Semanal",
        help_text="Número de veces que debe aparecer este grupo de alimentos en la semana"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )

    class Meta:
        db_table = 'nutricion_requerimientos_semanales'
        verbose_name = "Requerimiento Semanal"
        verbose_name_plural = "Requerimientos Semanales"
        ordering = ['modalidad', 'grupo']
        unique_together = [['modalidad', 'grupo']]
        indexes = [
            models.Index(fields=['modalidad'], name='nutricion_r_modalid_e1a6d0_idx'),
            models.Index(fields=['grupo'], name='nutricion_r_grupo_idx'),
        ]

    def __str__(self):
        return f"{self.modalidad.modalidad} - {self.grupo.grupo_alimentos} (x{self.frecuencia}/semana)"


class MinutaPatronMeta(models.Model):
    """
    Metas de peso neto por componente, grupo, nivel y modalidad según la resolución.
    Esta tabla normalizada permite validar si las preparaciones cumplen con los rangos
    de peso establecidos en la Minuta Patrón.
    """
    id_modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.CASCADE,
        db_column='id_modalidad',
        verbose_name="Modalidad de Consumo",
        related_name='metas_minuta'
    )
    id_grado_escolar_uapa = models.ForeignKey(
        TablaGradosEscolaresUapa,
        on_delete=models.CASCADE,
        db_column='id_grado_escolar_uapa',
        verbose_name="Grado Escolar UAPA",
        related_name='metas_minuta'
    )
    id_componente = models.ForeignKey(
        ComponentesAlimentos,
        on_delete=models.CASCADE,
        db_column='id_componente',
        verbose_name="Componente de Alimento",
        related_name='metas_minuta'
    )
    id_grupo_alimentos = models.ForeignKey(
        GruposAlimentos,
        on_delete=models.CASCADE,
        db_column='id_grupo_alimentos',
        verbose_name="Grupo de Alimentos",
        related_name='metas_minuta'
    )
    peso_neto_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Peso Neto Mínimo (g)"
    )
    peso_neto_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Peso Neto Máximo (g)"
    )

    class Meta:
        db_table = 'nutricion_minuta_patron_rangos'
        verbose_name = "Meta de Minuta Patrón"
        verbose_name_plural = "Metas de Minuta Patrón"
        unique_together = [['id_modalidad', 'id_grado_escolar_uapa', 'id_componente', 'id_grupo_alimentos']]

    def __str__(self):
        return f"{self.id_modalidad.modalidad} - {self.id_grado_escolar_uapa.nivel_escolar_uapa} - {self.id_componente.componente}"


class GrupoExcluyenteSet(models.Model):
    """
    Define un conjunto de grupos de alimentos que comparten una cuota semanal.
    Los grupos del mismo set son excluyentes entre sí: el total de apariciones
    de TODOS los grupos del set debe cumplir con frecuencia_compartida (no cada uno por separado).

    Ejemplo: G4 y G6 comparten cuota de 2/semana → G4+G6 ≥ 2, no G4≥2 Y G6≥2.
    """
    modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.CASCADE,
        db_column='id_modalidades',
        verbose_name="Modalidad de Consumo",
        related_name='grupos_excluyentes_sets'
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Set",
        help_text="Nombre descriptivo. Ej: 'G4-G6 proteína excluyente'"
    )
    frecuencia_compartida = models.IntegerField(
        verbose_name="Frecuencia Compartida",
        help_text="Veces/semana que debe aparecer CUALQUIERA de los grupos del set en conjunto"
    )

    class Meta:
        db_table = 'nutricion_grupo_excluyente_set'
        verbose_name = "Set de Grupos Excluyentes"
        verbose_name_plural = "Sets de Grupos Excluyentes"
        ordering = ['modalidad', 'nombre']

    def __str__(self):
        return f"{self.modalidad.modalidad} — {self.nombre} ({self.frecuencia_compartida}x/sem)"


class GrupoExcluyenteSetMiembro(models.Model):
    """
    Grupo de alimentos perteneciente a un set de exclusión.
    """
    set_excluyente = models.ForeignKey(
        GrupoExcluyenteSet,
        on_delete=models.CASCADE,
        related_name='miembros',
        verbose_name="Set Excluyente"
    )
    grupo = models.ForeignKey(
        GruposAlimentos,
        on_delete=models.CASCADE,
        related_name='sets_excluyentes',
        verbose_name="Grupo de Alimentos"
    )

    class Meta:
        db_table = 'nutricion_grupo_excluyente_set_miembro'
        unique_together = [['set_excluyente', 'grupo']]
        verbose_name = "Miembro del Set Excluyente"
        verbose_name_plural = "Miembros del Set Excluyente"

    def __str__(self):
        return f"{self.set_excluyente.nombre} ← {self.grupo.grupo_alimentos}"


class RestriccionAlimentoSubgrupo(models.Model):
    """
    Sub-restricción dentro de un grupo: de las apariciones del grupo en una semana,
    al menos `frecuencia` deben usar un alimento de la lista blanca.

    Ejemplo: G4 aparece 5 veces/semana, pero 2 de ellas deben ser leguminosas.
    """
    modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.CASCADE,
        db_column='id_modalidades',
        verbose_name="Modalidad de Consumo",
        related_name='restricciones_subgrupo'
    )
    grupo = models.ForeignKey(
        GruposAlimentos,
        on_delete=models.CASCADE,
        verbose_name="Grupo de Alimentos",
        related_name='restricciones_subgrupo'
    )
    nombre = models.CharField(
        max_length=120,
        verbose_name="Nombre de la Sub-restricción",
        help_text="Ej: 'G4 Leguminosas', 'G4 Huevo obligatorio'"
    )
    frecuencia = models.IntegerField(
        verbose_name="Frecuencia Requerida",
        help_text="Cuántas veces por semana debe usarse un alimento de la lista blanca"
    )

    class Meta:
        db_table = 'nutricion_restriccion_alimento_subgrupo'
        verbose_name = "Sub-restricción de Alimento"
        verbose_name_plural = "Sub-restricciones de Alimentos"
        ordering = ['modalidad', 'grupo', 'nombre']

    def __str__(self):
        return f"{self.modalidad.modalidad} — {self.nombre} (×{self.frecuencia}/sem)"


class RestriccionAlimentoEspecifico(models.Model):
    """
    Alimento válido para cumplir una RestriccionAlimentoSubgrupo.
    """
    restriccion = models.ForeignKey(
        RestriccionAlimentoSubgrupo,
        on_delete=models.CASCADE,
        related_name='alimentos',
        verbose_name="Sub-restricción"
    )
    alimento = models.ForeignKey(
        TablaAlimentos2018Icbf,
        on_delete=models.CASCADE,
        to_field='codigo',
        db_column='codigo_alimento',
        related_name='restricciones_subgrupo',
        verbose_name="Alimento ICBF"
    )

    class Meta:
        db_table = 'nutricion_restriccion_alimento_especifico'
        unique_together = [['restriccion', 'alimento']]
        verbose_name = "Alimento de Sub-restricción"
        verbose_name_plural = "Alimentos de Sub-restricciones"

    def __str__(self):
        return f"{self.restriccion.nombre} ← {self.alimento.nombre_del_alimento}"


class RecomendacionDiariaGradoMod(models.Model):
    """
    Recomendación nutricional diaria oficial ICBF por nivel escolar y modalidad de consumo.
    Actúa como denominador para calcular el porcentaje de adecuación del menú:
        porcentaje_calorias = (total_calorias / calorias_kcal) * 100
    """
    id_calorias_nivel_escolar = models.CharField(
        max_length=20,
        primary_key=True,
        verbose_name="ID Recomendación"
    )
    calorias_kcal = models.DecimalField(
        max_digits=8, decimal_places=1,
        verbose_name="Calorías (kcal)"
    )
    proteina_g = models.DecimalField(
        max_digits=7, decimal_places=1,
        verbose_name="Proteína (g)"
    )
    grasa_g = models.DecimalField(
        max_digits=7, decimal_places=1,
        verbose_name="Grasa (g)"
    )
    cho_g = models.DecimalField(
        max_digits=8, decimal_places=1,
        verbose_name="CHO (g)"
    )
    calcio_mg = models.DecimalField(
        max_digits=8, decimal_places=1,
        verbose_name="Calcio (mg)"
    )
    hierro_mg = models.DecimalField(
        max_digits=6, decimal_places=1,
        verbose_name="Hierro (mg)"
    )
    sodio_mg = models.DecimalField(
        max_digits=8, decimal_places=1,
        verbose_name="Sodio (mg)"
    )
    nivel_escolar_uapa = models.ForeignKey(
        TablaGradosEscolaresUapa,
        on_delete=models.PROTECT,
        db_column='nivel_escolar_uapa',
        verbose_name="Nivel Escolar",
        related_name='recomendaciones_diarias'
    )
    id_modalidades = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.PROTECT,
        db_column='id_modalidades',
        verbose_name="Modalidad",
        related_name='recomendaciones_diarias'
    )

    class Meta:
        db_table = 'nutricion_recomendacion_diaria_por_grado_mod'
        unique_together = [['nivel_escolar_uapa', 'id_modalidades']]
        verbose_name = "Recomendación Diaria por Grado y Modalidad"
        verbose_name_plural = "Recomendaciones Diarias por Grado y Modalidad"

    def __str__(self):
        return f"{self.nivel_escolar_uapa_id} - {self.id_modalidades_id}"
