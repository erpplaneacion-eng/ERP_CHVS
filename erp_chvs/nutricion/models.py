from django.db import models

class PermisosNutricion(models.Model):

    # ¡IMPORTANTE! 'class Meta' debe estar indentada
    # (con 4 espacios o 1 tab) para que esté DENTRO de PermisosNutricion.
    class Meta:
        verbose_name_plural = "Permisos de Nutrición"
        permissions = [
            ("view_contenido_nutricion", "Puede ver el contenido del módulo de nutrición"),
        ]
        
class TablaAlimentos2018Icbf(models.Model):
    codigo = models.CharField(primary_key=True, max_length=20)
    nombre_del_alimento = models.CharField(max_length=200)
    parte_analizada = models.CharField(max_length=100, blank=True, null=True)
    humedad_g = models.DecimalField(max_digits=10, decimal_places=2)
    energia_kcal = models.IntegerField()
    energia_kj = models.IntegerField()
    proteina_g = models.DecimalField(max_digits=10, decimal_places=2)
    lipidos_g = models.DecimalField(max_digits=10, decimal_places=2)
    carbohidratos_totales_g = models.DecimalField(max_digits=10, decimal_places=2)
    carbohidratos_disponibles_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fibra_dietaria_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cenizas_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    calcio_mg = models.IntegerField(blank=True, null=True)
    hierro_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sodio_mg = models.IntegerField(blank=True, null=True)
    fosforo_mg = models.IntegerField(blank=True, null=True)
    yodo_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    zinc_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    magnesio_mg = models.IntegerField(blank=True, null=True)
    potasio_mg = models.IntegerField(blank=True, null=True)
    tiamina_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    riboflavina_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    niacina_mg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    folatos_mcg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    vitamina_b12_mcg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    vitamina_c_mg = models.IntegerField(blank=True, null=True)
    vitamina_a_er = models.IntegerField(blank=True, null=True)
    grasa_saturada_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    grasa_monoinsaturada_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    grasa_poliinsaturada_g = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    colesterol_mg = models.IntegerField(blank=True, null=True)
    parte_comestible_field = models.IntegerField(db_column='parte_comestible_porcentaje', blank=True, null=True)  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.

    class Meta:
        managed = True  # Cambiado a True para permitir operaciones de escritura
        db_table = 'TABLA_ALIMENTOS_2018_ICBF'
        verbose_name = 'Alimento ICBF 2018'
        verbose_name_plural = 'Alimentos ICBF 2018'
    
    def __str__(self):
        return self.nombre_del_alimento