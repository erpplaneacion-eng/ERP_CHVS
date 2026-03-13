# MEJORAS FUTURAS — Módulo Contabilidad

Este documento describe las notificaciones automáticas pendientes de implementar.

---

## 1. Notificaciones por Gmail API

### Evento: Envío del registro (BORRADOR/DEVUELTO → ENVIADO)
- **Disparador**: `ContabilidadService.enviar()` exitoso
- **Destinatario**: Equipo de Compras (lista de correos configurada en settings)
- **Contenido sugerido**:
  > Asunto: [Contabilidad] Nuevo registro RC-{id} enviado por {lider_nombre}
  > Cuerpo: El líder {lider_nombre} ha enviado el registro RC-{id} de tipo {tipo} para el período {mes}/{año}.
  > Total: {valor_total} | Facturas: {num_facturas}
  > Ingrese al sistema para confirmar la recepción de documentos físicos.
- **Dependencias técnicas**: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`. Credenciales OAuth 2.0 en `.env` (`GMAIL_CREDENTIALS_JSON`, `GMAIL_TOKEN_JSON`).

### Evento: Devolución (EN_REVISION_COMPRAS → DEVUELTO_COMPRAS)
- **Disparador**: `ContabilidadService.devolver_compras()` exitoso
- **Destinatario**: El líder dueño del registro (`registro.lider.email`)
- **Contenido sugerido**:
  > Asunto: [Contabilidad] RC-{id} devuelto — requiere corrección
  > Cuerpo: El área de Compras ha devuelto su registro RC-{id}.
  > Motivo: {comentario}
  > Por favor corrija y reenvíe a la brevedad.

### Evento: Aprobación por Compras (EN_REVISION_COMPRAS → APROBADO_COMPRAS)
- **Disparador**: `ContabilidadService.aprobar_compras()` exitoso
- **Destinatario**: Equipo de Contabilidad (lista de correos en settings)
- **Contenido sugerido**:
  > Asunto: [Contabilidad] RC-{id} aprobado por Compras — pendiente revisión final
  > Cuerpo: El registro RC-{id} de {lider_nombre} fue aprobado por Compras.
  > Ingrese al sistema para realizar la revisión final de Contabilidad.

### Evento: Observación de Contabilidad (APROBADO_COMPRAS → OBSERVADO_CONTABILIDAD)
- **Disparador**: `ContabilidadService.observar_contabilidad()` exitoso
- **Destinatario**: Equipo de Compras
- **Contenido sugerido**:
  > Asunto: [Contabilidad] RC-{id} observado — respuesta requerida por Compras
  > Cuerpo: Contabilidad ha enviado una observación sobre el registro RC-{id}.
  > Observación: {comentario}
  > Por favor responda en el sistema para continuar el proceso.

### Evento: Cierre del registro (APROBADO_CONTABILIDAD → CERRADO)
- **Disparador**: `ContabilidadService.aprobar_contabilidad()` exitoso
- **Destinatario**: El líder dueño del registro
- **Contenido sugerido**:
  > Asunto: [Contabilidad] RC-{id} cerrado exitosamente
  > Cuerpo: Su registro RC-{id} del período {mes}/{año} ha sido aprobado y cerrado por Contabilidad.
  > Total procesado: {valor_total}

---

## 2. Notificaciones por WhatsApp (Meta Cloud API)

Seguir el patrón existente en `calidad/` (ver `erp_chvs/WHATSAPP_BOT_INTEGRACION.md`).
El servicio externo `apiw` (FastAPI en Railway, proyecto `developers-facebook`) ya tiene integración con Meta Cloud API.

### Arquitectura sugerida
```
Evento en ERP → ContabilidadService → POST a apiw /contabilidad/notificar/
    → apiw construye mensaje WhatsApp
    → Meta Cloud API → WhatsApp del destinatario
```

### Mapeo de eventos a notificaciones WhatsApp

| Evento | Destinatario | Mensaje sugerido |
|--------|-------------|-----------------|
| Envío del registro | Coordinador de Compras (teléfono en settings) | "📋 RC-{id}: {lider} envió un registro {tipo} por ${valor}. Confirme recepción en el sistema." |
| Devolución | Líder (teléfono en `PerfilUsuario.telefono`) | "⚠️ RC-{id} devuelto por Compras. Motivo: {motivo}. Corrija y reenvíe." |
| Aprobación por Compras | Coordinador de Contabilidad | "✅ RC-{id} aprobado por Compras. Pendiente revisión de Contabilidad." |
| Observación Contabilidad | Coordinador de Compras | "💬 RC-{id}: Contabilidad observó: {observación}. Responda en el sistema." |
| Cierre | Líder | "🎉 RC-{id} cerrado. Período {mes}/{año} procesado exitosamente." |

### Dependencias técnicas necesarias
1. **En `apiw`**: Crear endpoint `POST /contabilidad/notificar/` que acepte `{evento, registro_id, destinatario_tel, mensaje}` y llame a Meta Cloud API con plantilla o mensaje libre.
2. **En ERP (`contabilidad/services.py`)**: Añadir `_notificar_whatsapp(evento, registro, destinatario_tel)` que llame a `apiw` con autenticación compartida (`CALIDAD_WA_API_KEY`).
3. **En `.env`**: `CONTABILIDAD_COMPRAS_TEL`, `CONTABILIDAD_CONTABILIDAD_TEL` (teléfonos de los coordinadores de área, con código de país, ej: `573001234567`).
4. **Requerimiento de registro de plantillas en Meta**: Si se usan mensajes de plantilla (`template`), deben estar registradas y aprobadas en Meta Business Manager. Para mensajes libres solo funciona dentro de la ventana de 24h tras un mensaje del usuario.

### Notas
- El número de teléfono del líder se tomaría de `PerfilUsuario.telefono` (ya existe el campo en el modelo).
- Si el líder no tiene teléfono registrado, omitir la notificación WhatsApp y solo enviar email.
- Registrar intentos fallidos en `RegistroActividad` sin interrumpir el flujo principal.
