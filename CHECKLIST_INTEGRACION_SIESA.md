# ✅ Checklist de Información para Integración con Siesa

## Información a Solicitar al Equipo de TI / Proveedor Siesa

### 1. Credenciales de API

- [ ] **URL Base de la API**: _______________________________
- [ ] **Método de autenticación**:
  - [ ] API Key/Token
  - [ ] Usuario + Contraseña
  - [ ] OAuth 2.0 (Client ID + Secret)
  - [ ] Otro: _______________________
- [ ] **Credenciales**:
  - Usuario/Client ID: _______________________________
  - Contraseña/Token/Secret: _______________________________
  - ID Compañía: _______________________________

### 2. Endpoints Disponibles

#### Materias Primas / Ingredientes
- [ ] **Endpoint**: _______________________________
- [ ] **Método**: GET / POST / Otro: _______
- [ ] **Documentación**: (adjuntar link o PDF)

#### Precios de Compra
- [ ] **Endpoint**: _______________________________
- [ ] **¿Viene en el mismo endpoint de materias primas?**: Sí / No
- [ ] **Documentación**: (adjuntar link o PDF)

#### Sedes Educativas
- [ ] **Endpoint**: _______________________________
- [ ] **Método**: GET / POST / Otro: _______
- [ ] **Documentación**: (adjuntar link o PDF)

### 3. Ejemplo de Respuestas (CRÍTICO)

Por favor, solicitar **ejemplos reales** de las respuestas JSON/XML de cada endpoint:

#### Ejemplo Materias Primas
```json
{
  // PEGAR AQUÍ RESPUESTA REAL DE LA API
}
```

#### Ejemplo Precios
```json
{
  // PEGAR AQUÍ RESPUESTA REAL DE LA API
}
```

#### Ejemplo Sedes
```json
{
  // PEGAR AQUÍ RESPUESTA REAL DE LA API
}
```

### 4. Mapeo de Campos

#### Para Materias Primas → TablaIngredientesSiesa

| Campo en Django | Campo en Siesa | Ejemplo de Valor |
|----------------|----------------|------------------|
| codigo_siesa | | |
| descripcion | | |
| unidad_medida | | |
| precio | | |
| codigo_barras (si aplica) | | |
| categoria (si aplica) | | |

#### Para Sedes → SedesEducativas

| Campo en Django | Campo en Siesa | Ejemplo de Valor |
|----------------|----------------|------------------|
| codigo_sede | | |
| nombre | | |
| direccion (si aplica) | | |
| municipio | | |

### 5. Configuración Técnica

- [ ] **¿Siesa soporta Webhooks?**: Sí / No
  - Si SÍ:
    - URL de configuración: _______________________________
    - Eventos disponibles: _______________________________
    - Formato de payload: _______________________________

- [ ] **Rate Limits**:
  - Peticiones por minuto: _______
  - Peticiones por hora: _______
  - Peticiones por día: _______

- [ ] **Paginación**:
  - ¿Usa paginación?: Sí / No
  - Registros por página: _______
  - Parámetros de paginación: _______________________________

- [ ] **Versión de API**: _______________________________

- [ ] **Ambiente de pruebas disponible**: Sí / No
  - URL ambiente pruebas: _______________________________
  - Credenciales pruebas: _______________________________

### 6. Consideraciones Especiales

- [ ] **¿Los códigos de materias primas en Siesa coinciden con los códigos actuales en TablaIngredientesSiesa?**: Sí / No
  - Si NO: ¿Hay una tabla de equivalencias?

- [ ] **¿Las sedes en Siesa tienen el mismo código que en SedesEducativas?**: Sí / No
  - Si NO: ¿Cómo se mapean?

- [ ] **¿Hay campos obligatorios en Siesa que no existen en nuestro modelo Django?**: Sí / No
  - Si SÍ, listar: _______________________________

- [ ] **¿Los precios incluyen IVA?**: Sí / No

- [ ] **¿Qué moneda usan?**: COP / USD / Otra: _______

### 7. Contactos

- **Persona de contacto TI Siesa**: _______________________________
- **Email**: _______________________________
- **Teléfono**: _______________________________
- **Horario de soporte**: _______________________________

---

## 📝 Notas Adicionales

(Espacio para notas, observaciones, o cualquier información adicional relevante)

---

**Fecha de inicio de recopilación**: _______________________________
**Responsable**: _______________________________
**Fecha estimada de completitud**: _______________________________
