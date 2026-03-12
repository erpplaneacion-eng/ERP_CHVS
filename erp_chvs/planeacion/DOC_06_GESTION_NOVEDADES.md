# Documento 6: Gestión de Novedades (Cambios de Última Hora)

Este es uno de los escenarios más críticos en la operación real del PAE. La planeación funciona en el vacío (15 días antes todo es perfecto), pero el día a día está lleno de **Novedades** (huelgas, daños en acueductos, reducción de asistencia).

Dado que tu sistema `planeacion` está conectado asíncronamente a `SIESA` (el sistema contable/inventarios), cambiar un número no es tan simple como editar una celda en Excel.

Para resolver este desafío, el módulo debe implementar el motor de **Gestión de Novedades Operativas**.

---

## 1. El Concepto Funcional

A nivel de interfaz, no podemos permitir que un usuario simplemente "edite" el campo `raciones` de un despacho consolidado, porque perderíamos la trazabilidad fiscal. Toda reducción o aumento debe registrarse por separado con un *motivo* legal.

Debemos crear un modelo nuevo en `planeacion/models.py`:

```python
class NovedadOperativa(models.Model):
    despacho = models.ForeignKey('Despacho', on_delete=models.CASCADE)
    sede_afectada = models.ForeignKey('SedesEducativas', on_delete=models.PROTECT)
    fecha_novedad = models.DateField(auto_now_add=True)
    
    raciones_originales = models.IntegerField()
    raciones_finales = models.IntegerField()  # ej: bajó de 200 a 150
    
    MOTIVOS = [
        ('paro_docente', 'Paro / Cese de Actividades'),
        ('clima', 'Emergencia Climática'),
        ('acueducto', 'Corte de Servicio de Agua/Luz'),
        ('inasistencia', 'Baja asistencia estudiantil')
    ]
    motivo = models.CharField(max_length=50, choices=MOTIVOS)
    observaciones = models.TextField()
    
    estado_siesa = models.CharField(max_length=20, default='pendiente_ajuste')
```

---

## 2. Los Dos Escenarios de la Novedad (El Tiempo es Clave)

El impacto de una novedad depende de **DÓNDE** está el documento de despacho en ese preciso segundo. Existen dos paredes de tiempo:

### Escenario A: "Aún no ha viajado a SIESA" (Fácil)
- **Estado del Despacho:** `borrador` o `aprobado`.
- **Qué ocurre:** La escuela avisa hoy 12 de marzo que el 16 de marzo no habrá agua y bajan raciones. Como el Despacho #1001 aún no se ha mandado a SIESA mediante el JSON, el sistema simplemente:
  1. Registra la `NovedadOperativa` en la base de datos.
  2. Actualiza callado el número de raciones en `ProgramacionMenus`.
  3. Al momento en que el operador logístico oprima "Procesar a SIESA" 2 días después, la matemática se hará con las 150 raciones nuevas. **Cero dolor.**

### Escenario B: "Ya se generó el documento (RQI/SC) en SIESA" (Complejo)
- **Estado del Despacho:** `siesa_integrado` (Ya existe el folio RQI-9945 en el ERP financiero).
- **Qué ocurre:** SIESA "ya separó" y costeo en sus bodegas 17.5 kilos de arroz usando la RQI-9945. No podemos enviar otro JSON modificando una RQI aprobada por el gerente en SIESA.

---

## 3. Solución Tecnológica Propuesta para el Escenario B

Cuando `planeacion` detecta que se está registrando una `NovedadOperativa` sobre un despacho cuyo estado es `siesa_integrado`, el motor del módulo `Api/` debe ejecutar un protocolo inverso:

**Flujo de Devolución/Ajuste Automatizado:**

1. **Recálculo de la Diferencia:** El sistema resta 200 originales - 150 nuevas = **50 raciones sobrantes**.
2. **Cálculo Nutricional Inverso:** ¿Cuántos gramos de 'Arroz blanco crudo' equivalen a 50 raciones menú #1? -> 2,500 gramos.
3. **Equivalencia SIESA Inversa:** ¿Cuántos Bultos/Bolsas de SIESA equivalen a esos 2,500 gramos? -> 0.05 Unidades.
4. **Disparador a la API:** El módulo `Api/` ensambla un documento SIESA distinto.
   - Si los insumos aún no han salido en los camiones: Se lanza un **Documento de Ajuste o Reversión de RQI** (Dependiendo de la configuración contable que maneje el SIESA de la Corporación, usualmente un ajuste de inventario o cancelación parcial de línea).
   - Si los insumos ya salieron: Se registra la Novedad en `planeacion` pero se alerta que el reintegro físico se debe tramitar desde Bodega (módulo Logística/Aseo de Supply Controller).

## 4. Diseño del Módulo Gerencial: "Gestión de Novedades"

Para soportar esto sin que sea un dolor de cabeza en el día a día para operadores que no son contadores, la UI de `planeacion` debe tener una pantalla dedicada: **Gestión de Novedades**.

- **Flujo UI del Operador:**
  1. El operador recibe la llamada de la coordinadora de la institución.
  2. Entra a `Novedades -> Registrar Novedad`.
  3. Búsqueda rápida: `Sede = I.E. B`, `Fecha Afectada = 30 Marzo`.
  4. El sistema trae el Despacho comprometido.
  5. El operador cambia un "Input" de `200` a `150`, elige motivo "Corte de Agua" y da "Guardar".

- **La Magia por Debajo:**
  El operador se desentiende. El sistema por debajo verifica "el estado del despacho". 
  Si no ha sido enviado, hace el Update local.
  Si ya fue enviado, levanta un cronjob en cola a la app `Api/` para que hable con SIESA mandando un ajuste negativo de la requisición original. Todo totalmente transparente para el usuario logístico. 

**(Nota Crítica para el desarrollo):** Para construir el protocolo del Escenario B en la segunda fase, es vital preguntar a los consultores funcionales de SIESA con qué "Tipo de Documento" (Siglas en SIESA) se hace una reversión automática de RQI en el ERP contable de ellos.
