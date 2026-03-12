# Documento 2: Arquitectura y Modelos de Datos para Despachos en `planeacion`

Para llevar el flujo operativo de Supply Controller ("Generar Despacho" y "Consultar Despacho") a la aplicación `planeacion` de ERP_CHVS e integrarlo con `nutricion` y `SIESA`, necesitamos expandir el modelo de datos.

Actualmente, el archivo `PROPUESTA_INTEGRACION_SIESA.md` menciona el modelo `ProgramacionMenus`, el cual es la base, pero un "Despacho" es una entidad logística de nivel superior que agrupa múltiples sedes, menús e ingredientes para una ruta y fecha específica.

## 1. Arquitectura Relacional Propuesta

La estructura debe soportar las tres dimensiones del problema: **Qué** (el menú y sus ingredientes), **Dónde** (la sede y la ruta), y **Cuándo** (la fecha de entrega).

```
[logistica.Ruta] <───────┐
                         │
[planeacion.Despacho] ◄──┴─── [planeacion.ProgramacionMenus]
(Encabezado de la 
 orden de salida)            (Detalle por sede y menú)
      │
      └─────────► [Api.OrdenCompra / Api.RQI] (Hacia SIESA)
```

## 2. Nuevos Modelos a Implementar en `planeacion/models.py`

### A. Modelo `Despacho` (La Orden de Salida)
Agrupa las programaciones individuales en un "paquete" logístico manejable. Este es el registro que se visualiza en el calendario de "Consultar Despacho".

```python
class Despacho(models.Model):
    """
    Agrupa un conjunto de programaciones de menú para una fecha y ruta específica.
    Equivale a una "Orden de Salida" o la base para una RQI/SC hacia SIESA.
    """
    from logistica.models import Ruta
    
    fecha_despacho = models.DateField(verbose_name="Fecha del Despacho")
    id_programa = models.ForeignKey('Programa', on_delete=models.PROTECT)
    ruta_entrega = models.ForeignKey(Ruta, on_delete=models.PROTECT)
    
    ESTADO_DESPACHO = [
        ('borrador', 'Borrador (Solo Proyección)'),
        ('aprobado', 'Aprobado / Generado'),
        ('en_transito', 'En Tránsito'),
        ('entregado', 'Entregado a Sedes'),
        ('siesa_integrado', 'Integrado SIESA (SC/RQI Generada)')
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_DESPACHO, default='borrador')
    
    # Datos de integración con SIESA (se llenan asíncronamente vía Api/)
    numero_sc_siesa = models.CharField(max_length=50, blank=True, null=True)
    numero_rqi_siesa = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'planeacion_despacho'
        unique_together = [['fecha_despacho', 'id_programa', 'ruta_entrega']]
```

### B. Modificación a `ProgramacionMenus` (El Detalle)
Se debe añadir la relación foránea hacia la nueva cabecera de `Despacho`.

```python
class ProgramacionMenus(models.Model):
    # Campos existentes...
    fecha = models.DateField()
    sede_educativa = models.ForeignKey(...)
    id_menu = models.ForeignKey(...)
    raciones = models.IntegerField()
    # ...
    
    # NUEVO CAMPO RELACIONAL:
    id_despacho = models.ForeignKey(
        Despacho, 
        on_delete=models.CASCADE, 
        related_name='programaciones_sede',
        null=True, 
        blank=True
    )
```

## 3. Lógica del Flujo de Datos (Servicios)

El traslado de datos desde la UI hacia SIESA requiere un `service.py` robusto en `planeacion`:

1.  **UI "Generar Proyección/Despacho":** El usuario cruza un `Rango de Fechas` + `Programa` + `Modalidad`. El sistema lee `logistica_ruta_sedes` e inserta los registros masivos en `ProgramacionMenus`.
2.  **Agrupación:** El sistema agrupa los registros de `ProgramacionMenus` por `Fecha` y `Ruta` y crea los encabezados en la tabla `Despacho`.
3.  **Cálculo Insumos (`calcular_necesidades_compra()`):** Toma un ID de `Despacho`, busca sus programaciones, cruza con `nutricion_tabla_preparacion_ingredientes` (multiplicado por raciones) y aplica el `EquivalenciaICBFCompras` para obtener las unidades de la bodega de SIESA.
4.  **Disparador SIESA:** Al cambiar el estado del `Despacho` a 'aprobado', se llama asíncronamente a los conectores de la app `Api/` para hacer el POST del JSON de la SC/RQI.

## 4. Ventajas de esta Arquitectura
- **Independencia Logística:** SIESA no necesita saber qué menú comen los niños. SIESA solo recibe "Se requieren X unidades de Atún en la bodega Y". La granularidad del PAE (menús, gramajes, ICBF) se queda localmente en Postgres, protegiendo al ERP financiero de basura de datos operativos.
- **Trazabilidad Pura:** Desde el folio de una SC en SIESA, el sistema puede rastrear exactamente hacia qué escuelas (`SedesEducativas`), por qué `Ruta`, y en base a qué `Menú` (diseñado por Nutrición) se originó ese gasto.
