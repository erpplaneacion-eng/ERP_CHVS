from django.db import models

# Create your models here.

class PrincipalDepartamento(models.Model):
    codigo_departamento = models.CharField(max_length=100, primary_key=True)
    nombre_departamento = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_departamento

    class Meta:
        verbose_name = "Departamento"
        db_table = 'principal_departamento'
        
class PrincipalMunicipio(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo_municipio = models.IntegerField()
    nombre_municipio = models.CharField(max_length=100)
    codigo_departamento = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre_municipio
    

    class Meta:
        managed = True
        db_table = 'principal_municipio'


# Modelo para la tabla: tipo_documento
class TipoDocumento(models.Model):
    # varchar2 [pk, not null, unique] se traduce a CharField con primary_key=True.
    # Necesita un max_length, por ejemplo 10 caracteres.
    id_documento = models.CharField(max_length=10, primary_key=True, verbose_name="ID Documento")

    # varchar2 se traduce a CharField.
    tipo_documento = models.CharField(max_length=100, verbose_name="Tipo de Documento")

    # integer se traduce a IntegerField.
    codigo_documento = models.IntegerField(verbose_name="Código Documento")

    class Meta:
        # Nombre de la tabla en la base de datos.
        db_table = 'tipo_documento'
        # Nombres para el panel de administración de Django.
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documento'

    def __str__(self):
        # Representación en texto del objeto (útil en el admin).
        return self.tipo_documento


# Modelo para la tabla: tipo_genero
class TipoGenero(models.Model):
    id_genero = models.CharField(max_length=10, primary_key=True, verbose_name="ID Género")
    genero = models.CharField(max_length=50, verbose_name="Género")
    codigo_genero = models.IntegerField(verbose_name="Código Género")

    class Meta:
        db_table = 'tipo_genero'
        verbose_name = 'Tipo de Género'
        verbose_name_plural = 'Tipos de Género'

    def __str__(self):
        return self.genero


# Modelo para la tabla: modalidades_de_consumo
# Nota: Corregí el nombre de la tabla de "modalides" a "modalidades".
class ModalidadesDeConsumo(models.Model):
    id_modalidades = models.CharField(max_length=10, primary_key=True, verbose_name="ID Modalidad")
    modalidad = models.CharField(max_length=150, verbose_name="Modalidad")
    cod_modalidad = models.CharField(max_length=20, verbose_name="Código de Modalidad")

    class Meta:
        db_table = 'modalidades_de_consumo'
        verbose_name = 'Modalidad de Consumo'
        verbose_name_plural = 'Modalidades de Consumo'

    def __str__(self):
        return self.modalidad