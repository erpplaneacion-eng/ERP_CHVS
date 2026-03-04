# Diseño: Tarjetas de Menús con Estado y Lista de Preparaciones

Fecha: 2026-03-04
Módulo: Nutrición (`/nutricion/menus/`)

## Objetivo
Corregir la diferenciación visual entre menús con/sin preparaciones y permitir visualizar rápidamente las preparaciones de cada menú desde la tarjeta.

## Alcance
1. Backend de `/nutricion/api/menus/` para enviar:
- `tiene_preparaciones` (bool por menú)
- `preparaciones` (lista completa de nombres por menú)
2. Frontend de tarjetas para mostrar:
- Resumen persistente (`N preparaciones` o `Sin preparaciones`)
- Lista completa en panel flotante (hover en desktop, click/tap en móvil)
3. Estilos CSS para panel compacto, legible y con scroll.

## Decisión UX
Se adopta enfoque híbrido:
1. Estado visible siempre en tarjeta.
2. Lista completa bajo demanda:
- Hover en escritorio.
- Click/tap mediante toggle para dispositivos táctiles.

Esto evita tarjetas excesivamente altas y mantiene acceso rápido a toda la información.

## Datos y Flujo
1. `api_menus` consulta menús del programa.
2. Se resuelven preparaciones por `id_menu`.
3. Cada menú se serializa con:
- `preparaciones: string[]`
- `tiene_preparaciones: boolean`
4. `ModalidadesManager` consume ambos campos al renderizar tarjetas regulares y especiales.

## Manejo de Seguridad/Robustez
1. Los nombres de preparaciones se escapan en frontend antes de inyectarse en HTML.
2. El panel de lista usa `max-height` + `overflow-y:auto` para listas largas.

## Validación esperada
1. Menú sin preparaciones:
- Tarjeta sin clase `has-preparaciones`
- Resumen: `Sin preparaciones`
2. Menú con preparaciones:
- Tarjeta con clase `has-preparaciones`
- Resumen: `N preparaciones`
- Hover/click muestra lista completa

