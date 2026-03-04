# Diseño: Descarga PDF de Ciclo de Menús (20 menús)

Fecha: 2026-03-04
Módulo: Nutrición (`/nutricion/menus/`)

## Objetivo
Agregar, junto a los botones de descarga existentes por modalidad, un botón para descargar en PDF el ciclo completo de menús (1-20) para un programa/modalidad.

## Alcance funcional
1. Descarga por `programa_id + modalidad_id`.
2. Formato tabular por semanas:
- Semana 1: menús 1-5
- Semana 2: menús 6-10
- Semana 3: menús 11-15
- Semana 4: menús 16-20
3. Contenido de celdas:
- Mostrar solo nombre de preparación.
- Menú faltante: `PENDIENTE`.
- Componente sin preparación en menú existente: `N/A`.
4. Encabezado usa datos del programa (incluyendo logo de programa si existe).
5. Bloque final de firmas con configuración de `FirmaNutricionalContrato`.

## Diseño técnico
1. Servicio dedicado `CicloMenusPdfService` con `reportlab`.
2. View nueva `download_ciclo_menus_pdf`.
3. URL nueva:
`/nutricion/exportar-ciclo-menus-pdf/<programa_id>/<modalidad_id>/`
4. Botón nuevo en header de modalidad:
`Descargar Ciclo PDF`.

## Orden de componentes
Se respeta `ORDEN_COMPONENTES_POR_MODALIDAD` para mantener consistencia con exportaciones existentes.
Si hay componentes fuera del mapa, se agregan al final.

## Visibilidad del botón
Sigue la misma lógica de los botones de descarga de modalidad:
visible al completar los 20 menús (reactivo tras generar/copiar).

