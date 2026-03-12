# Documento 8: Visión Experta en Logística de Operaciones PAE (30 Años de Experiencia)

Como planificador logístico con 30 años en el ruedo, te digo esto: **el papel (y el software) lo aguantan todo, pero la calle es dura.** 

El diseño que tenemos hasta el Documento 7 es excelente matemáticamente y en sistemas. Pero la operación masiva de alimentos perecederos en escuelas públicas tiene variables ocultas que rompen los sistemas más robustos si no se prevén.

Aquí tienes 5 consideraciones operativas del "mundo real" que el módulo de `planeacion` y `logistica` de **ERP_CHVS** debe tener en el radar (al menos como 'Fase 2' del proyecto):

---

## 1. El Enemigo #1: Cubicaje y Capacidad de los Vehículos

El sistema actualmente calcula que necesitamos despachar "50 Bultos de Arroz y 40 Bidones de Aceite". Matemáticamente es perfecto. SIESA genera la RQI. 
**Pero, ¿Caben en el furgón NHR asignado a la Ruta Centro?**

Las rutas no son infinitas. Tienen una asignación física a un vehículo con una **capacidad máxima de carga (Kilos) y volumen (Metros Cúbicos)**.
- **La Solución en Sistemas:** El catálogo de SIESA (`TablaIngredientesSiesa`) debe traer, además de los gramos del alimento, el **Peso Bruto del Empaque** y sus **Dimensiones (Volumen)**. 
- **La Alerta experta:** Cuando el operador hace clic en "Planear Despacho", el sistema debería lanzar una advertencia amarilla: *"Alerta: La Ruta Urbana Sur pesa 3.5 Toneladas, el furgón asociado (Placa XYZ-123) solo tiene capacidad para 3 Toneladas."* Esto evita que la bodega empaque algo que el chofer va a dejar tirado en el muelle.

## 2. Los Quiebres de Stock en Bodega (Manejo de Faltantes/Backorders)

El sistema le pide a SIESA 100 bolsas de leche. Pero en bodega, por culpa del proveedor, solo hay 80.
- **La realidad:** El camión TIENE que salir a las 4:00 AM. Si esperamos que el sistema "cuadre", los niños no desayunan.
- **Solución Dinámica:** Cuando la integración SIESA arroje error por "Falta de Saldo", el sistema en ERP_CHVS debe tener un botón de **"Forzar Despacho con Faltantes"**. 
Esto genera la RQI por las 80 unidades reales y deja un "Delta Pendiente" (20 unidades) asociado a la escuela, para que el sistema se acuerde de enviarlas en el *siguiente* despacho o el operador avise a la sede de la contingencia.

## 3. Ventanas Horarias de las Escuelas (El Caos Rural)

No puedes entregar a cualquier hora. 
- La Escuela A (Urbana) te recibe de 6:00 AM a 10:00 AM.
- La Escuela B (Rural) está a 2 horas de trocha y la ecónoma se va a las 11:00 AM.
- **Impacto Logístico:** El orden en que visitas las sedes en la tabla `RutaSedes` no es simplemente alfabético. Es un **Ruteo Cronológico**.
- **Solución a Futuro:** El módulo `logistica` debe contener en `SedesEducativas` los campos `hora_apertura` y `hora_cierre_recepcion`. Planeación debería imprimir la "Hoja de Ruta del Conductor" listando el orden exacto de entrega sugerido para no encontrar puertas cerradas.

## 4. Logística Inversa: Devoluciones y Rechazos

Llegaste a la sede. De los 5 quesos, la ecónoma revisa y te rechaza 1 porque perdió vacío o se rompió la bolsa. 
Ese queso vuelve al camión. 
*¿Cómo afecta esto al sistema?*
- SIESA ya descontó ese queso de su inventario principal en la RQI original.
- El camión regresa a bodega por la tarde.
- **El Flujo Necesario:** El módulo debe tener, ligado al `Despacho`, un submódulo de **"Cierre de Ruta / Legalización"**. Donde el conductor reporte: *"Regresé 1 queso partido de la Escuela X"*. Esto debe disparar a SIESA un "Documento de Entrada por Devolución" mandando el queso a una **Bodega de Averías/Mermas** (no al stock bueno).

## 5. Homologación de Productos de Emergencia (El Plan B Nutricional)

El menú dice: Sopa con Papa Guata.
Voy a bodega, ¡no llegó la Papa Guata! Pero tengo mucha Papa Parda. 
Para despachar la bodega toma la Papa Parda. 
- **El Problema Analítico:** Si SIESA descuenta Papa Parda, pero ERP_CHVS tiene registrado menú con Papa Guata, empieza el desastre en los históricos y las auditorías de MinEducación, porque el "Match ICBF" era con otro producto.
- **Solución Experta:** En la vista de `planeacion`, al mismo tiempo que el operador marca las rutas a despachar, debe tener la posibilidad de indicar: *"Sustitución aprobada por Nutricionista: Para este despacho, cambiaremos el alimento X por el alimento Y"*. Así el sistema altera el menú "al vuelo" solo para esa fecha y recalcula hacia SIESA usando el producto correcto, salvando la trazabilidad.

---
### Resumen del Viejo Planificador:
Construyan lo básico primero (los 7 documentos anteriores). Ese es el motor que hace que el carro ande.
Pero estos 5 puntos de arriba son los "sistemas de suspensión y frenos ABS". Son los que hacen que el software no se rompa cuando choca contra el barro y la realidad de repartir comida en colegios a las 5 de la mañana. Guarden este documento como su **Hoja de Ruta para la Fase 2 del módulo de Planeación**.
