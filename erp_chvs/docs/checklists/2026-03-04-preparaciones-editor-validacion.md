# Checklist de Validacion - Preparaciones Editor

Fecha: 2026-03-04
Scope: `nutricion/menus/<id_menu>/preparaciones-editor/`

## 1. Flujo Base
- [ ] Carga de la vista sin errores JS en consola.
- [ ] Render correcto de tabs por nivel.
- [ ] Guardar cambios de pesos por nivel funciona.
- [ ] Eliminar ingrediente desde fila funciona.
- [ ] Eliminar preparacion completa funciona.
- [ ] Renombrar preparacion inline funciona en todos los tabs.

## 2. Copia de Preparaciones
- [ ] Boton `Copiar desde otro menu` abre modal.
- [ ] Filtro de menu origen funciona por texto.
- [ ] Filtro de preparacion funciona por texto.
- [ ] Vista previa de ingredientes carga sin errores.
- [ ] Seleccionar todos / quitar todos checkboxes funciona.
- [ ] Validacion impide confirmar si no hay ingredientes seleccionados.
- [ ] Copia parcial (subset de ingredientes) funciona.
- [ ] Copia desde menu de misma modalidad funciona.
- [ ] Copia a modalidad distinta bloquea con mensaje de error.
- [ ] Tras copiar, la vista recarga y se ve la nueva preparacion.

## 3. Robustez UX
- [ ] No hay doble submit en copia (boton deshabilitado durante proceso).
- [ ] Mensajes de error son claros en fallos de red/API.
- [ ] Overlay de guardado/copia aparece y desaparece correctamente.

## 4. Auditoria
- [ ] RegistroActividad almacena:
  - [ ] menu origen
  - [ ] menu destino
  - [ ] nombre nueva preparacion
  - [ ] total ingredientes origen
  - [ ] total copiados
  - [ ] total excluidos

## 5. Calidad Tecnica
- [ ] `manage.py check` en verde.
- [ ] Tests de copia parcial y modalidad en verde.
- [ ] Sin texto mojibake en `preparaciones_editor.js` (`Ã`, `Â¿`, `â€”`, etc.).

