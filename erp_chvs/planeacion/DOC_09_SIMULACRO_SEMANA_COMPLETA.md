# Documento 9: Simulacro Semanal Avanzado de Despachos (ERP_CHVS)

A diferencia del primer simulacro ("Día en la Vida") que era lineal, este es un simulacro de **estrés de una semana completa operativa**. Pondremos a prueba todas las reglas documentadas de la Fase 1 y Fase 2 (Periodos, Novedades, Cubicación y Cadenas de Frío).

---

## 📅 CONTEXTO DE LA SEMANA: 16 al 20 de Marzo, 2026.

**Las piezas en el tablero:**
- **Ruta 1 (Urbana Centro):** 20 Escuelas. Capacidad del Furgón: 3.5 Toneladas.
- **Ruta 2 (Rural Montaña):** 5 Escuelas Lejanas. Capacidad de Camioneta mixta: 1.5 Toneladas. La escuela "Pico Seco" tiene etiqueta de `frecuencia = semanal`.
- **Menús:** Minutas 1 a la 5. Alta presencia de Congelados (Pollo/Carne) y Lácteos.

---

## 🎬 ACTO 1: LA PLANEACIÓN DEL VIERNES (DÍA CERO)

Es **Viernes 13 de Marzo, 2:00 PM**. El planeador abre el ERP_CHVS para surtir la comida de lunes a miércoles.

1. **Gestión Urbana (Ruta 1)**
   - El operador elige: `Ruta Urbana Centro`, `Fechas: 16, 17 y 18 de Marzo`.
   - El sistema totaliza matemáticamente las raciones de las 20 escuelas. 
   - *Regla de Categorías (Doc 07):* El sistema detecta que es Urbana. Automáticamente el código divide el peso logístico total. 
   - ERP_CHVS ensambla y envía **2 Documentos a SIESA**:
     - `SC-101`: Solo para los Alimentos Secos (Abarrotes).
     - `SC-102`: Solo para Lácteos y Carnes (Congelados).
   - *SIESA aprueba.* En la bodega, se imprimen dos *picking lists* para cargar el furgón seco y el termo-king.

2. **Gestión Rural (Ruta 2)**
   - El operador elige: `Ruta Rural Montaña`, `Fechas: 16, 17 y 18 de Marzo`.
   - *Regla de Excepción Semanal:* El sistema detecta a "Pico Seco" y sabe que el camión no volverá a subir allá el miércoles. Ocultamente le suma a "Pico Seco" la comida del 19 y 20 de marzo.
   - *Regla Rural:* El sistema **NO** divide por temperatura. 
   - ERP_CHVS ensambla y envía **1 Documento a SIESA**:
     - `SC-103`: Abarrotes + Congelados mezclados.
   - *Alerta de Cubicaje (Doc 08):* Pantalla amarilla saltando ⚠️: *"El peso de SC-103 sumado son 1.8 Toneladas, la camioneta Mountain solo aguanta 1.5. ¡Riesgo de Sobrecarga!"*.
   - El operador decide llamar al conductor y autorizan llevar un pequeño remolque. Aprueba el despacho e ignora el *warning*.

---

## 🎬 ACTO 2: EL MIÉRCOLES Y LAS NOVEDADES

Es **Miércoles 18 de Marzo, 9:00 AM**. Hay que planear Jueves (19) y Viernes (20).

1. **El impacto de las Excepciones**
   - El operador selecciona la `Ruta Rural Montaña` y pide fechas `19 y 20 de Marzo`.
   - El sistema calcula comida para 4 escuelas. **Ignora** por completo a "Pico Seco" porque cruza con las fechas ya despachadas el viernes pasado.
   - Se genera una orden limpia a SIESA: `SC-104`.

2. **La Novedad Urbana (El Caos)**
   - Suena el teléfono. La Escuela "Centro Mayor" (Urbana) informa: *Grave daño de acueducto, no habrá clases mañana jueves*.
   - **El Diagnóstico en el Sistema:** El operador abre el Tablero. Las raciones del jueves apenas las iba a pedir hoy al mediodía en el segundo bloque de despachos de la semana (Jue-Vie).
   - Es una novedad Escenario A (`Doc 06 - Fácil`): Se entra a la pantalla de **Novedades**, se busca Centro Mayor, y el jueves 19 se baja a `Cero Raciones`, motivo `Emergencia Acueducto`.
   - A las 2:00 PM, el planeador corre la generación de despachos `Urbanos 19-20`. El sistema procesa la orden `SC-105` y `SC-106` para SIESA, pero yendo con 500 raciones menos. **Dólares y kilos perfectamente ahorrados sin tocar a los contadores.**

---

## 🎬 ACTO 3: LA CALLE, LAS MERMAS Y EL RECHAZO (JUEVES AM)

Es **Jueves 19 de Marzo, 8:00 AM**. El furgón entregando la orden `SC-106` (Congelados Urbanos).

1. **Logística Inversa Obligada (`Doc 08`)**:
   - Entrega en "Escuela Simón Bolívar". La ecónoma revisa 15 paquetes de Pollo. Uno está desangrado (pérdida de frío/vacío). Firma la remisión con un asterisco: *"Rechazo 1 paquete"*.
   - El Pollo regresa al camión. Ese pollo no se le puede entregar a otra escuela. A las 2:00 PM el conductor llega a bodega a hacer su "cierre de ruta".
  
2. **Legalizando en ERP_CHVS:**
   - El despachador de bodega entra al Despacho asociado a la `SC-106`. Hace clic en **Legalizar/Cerrar Ruta**.
   - Ingresa: Sede: Simón Bolívar -> Sub-ítem Pollo -> Motivo: Mermas Calidad -> -1 Empaque.
   - ERP_CHVS ensambla un JSON automático por debajo mediante `Api/` y lo envía a SIESA: *"Hola SIESA, soy una entrada de Ajuste al Inventario. Recibe (1) unidad de Pollo y métela en la sub-bodega B04 (Averías y Mermas) y desmárcala de la orden de ventas de Escuela Simón Bolívar"*.
   - Trazabilidad perfecta. El auditor del ICBF ve por qué la escuela recibió menos proteína en sistema, y el contador ve la avería contable cuadrada.

---

## 📊 BALANCE FINAL DE LA SEMANA:

El **ERP_CHVS** (el orquestador) operó como una torre de control impecable:
1. Las escuelas recibieron los kilos exactos sin que el conductor tuviera que hacer cálculos matemáticos (`Doc 05`).
2. SIESA supo exactamente en qué camiones y en qué unidades comerciales entregar las cosas (`Doc 07`).
3. Planeación ahorró 500 raciones reaccionando milimétricamente al daño de acueducto en tiempo real (`Doc 06`).
4. Bodega y Contabilidad legalizaron el pollo dañado el mismo día, manteniendo sus Kardex y balances inmaculados (`Doc 08`).
