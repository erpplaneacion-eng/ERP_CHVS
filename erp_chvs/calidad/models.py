import datetime
from django.db import models
from django.contrib.auth.models import User


class CertificadoCalidad(models.Model):
    TIPO_EMPLEADO_CHOICES = [
        ('manipuladora', 'Manipuladora de Alimentos'),
        ('planta', 'Personal de Planta'),
        ('aprendiz', 'Aprendiz SENA'),
    ]

    numero_certificado = models.CharField(max_length=20, unique=True, editable=False)
    cedula = models.CharField(max_length=20, verbose_name='Cédula')
    nombre_completo = models.CharField(max_length=200, verbose_name='Nombre Completo')
    cargo = models.CharField(max_length=200, verbose_name='Cargo', blank=True)
    programa_empresa = models.CharField(max_length=300, verbose_name='Programa / Empresa', blank=True)
    eps = models.CharField(max_length=200, verbose_name='EPS', blank=True)
    tipo_empleado = models.CharField(
        max_length=20, choices=TIPO_EMPLEADO_CHOICES, verbose_name='Tipo de Empleado'
    )
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    fecha_emision = models.DateField(auto_now_add=True, verbose_name='Fecha de Emisión')
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name='Creado por'
    )

    class Meta:
        db_table = 'calidad_certificados'
        ordering = ['-fecha_emision', '-id']
        verbose_name = 'Certificado de Calidad'
        verbose_name_plural = 'Certificados de Calidad'

    def __str__(self):
        return f"{self.numero_certificado} - {self.nombre_completo}"

    def save(self, *args, **kwargs):
        if not self.numero_certificado:
            self.numero_certificado = self._generar_numero()
        super().save(*args, **kwargs)

    def _generar_numero(self):
        year = datetime.date.today().year
        count = CertificadoCalidad.objects.filter(fecha_emision__year=year).count() + 1
        return f"CC-{year}-{count:04d}"
