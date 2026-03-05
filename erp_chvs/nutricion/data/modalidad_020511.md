# Modalidad 020511 - Documentación de Datos

## Información General
- **ID Modalidad:** 020511
- **Programa ID:** 15

---

## 1. Rangos de Grados Escolares

| ID Grado | Nivel Escolar |
|----------|----------------|
| 100 | Preescolar |
| 123 | Primaria 1, 2, 3 |
| 45 | Primaria 4, 5 |
| 6789 | Secundaria |
| 1011 | Media ciclo complementario |

---

## 2. Componentes

| ID Componente | Nombre |
|---------------|--------|
| com2 | Alimento proteico |
| com3 | Cereal acompañante |
| com4 | Fruta |
| com5 | Azúcares |
| com11 | Leche y productos lácteos |
| com12 | Frutas |
| com13 | Postre |
| com14 | Bebida |
| com18 | (Nuevo) |

---

## 3. Grupos de Alimentos

| ID Grupo | Nombre |
|----------|--------|
| g1 | Grupo I. Cereales, raíces, tubérculos y plátanos |
| g2 | Grupo II. Fruta y verduras |
| g3 | Grupo III. Leche y productos lácteos |
| g4 | Grupo IV. Carnes, huevos, leguminosas secas, frutos secos y semillas |
| g6 | Grupo VI. Azúcares |

---

## 4. Rangos de Peso Neto - TABLA COMPLETA (nutricion_minuta_patron_rangos)

### Preescolar (100)
| ID | Componente | Grupo | Peso Mín (g) | Peso Máx (g) |
|-----|------------|-------|--------------|--------------|
| 201 | com11 | g3 | 180 | 180 |
| 202 | com12 | g2 | 100 | null |
| 203 | com13 | g4 | 12 | 40 |
| 204 | com3 | g1 | 12 | 40 |
| 205 | com4 | g2 | 100 | 0 |
| 226 | com5 | g6 | 5 | 7 |
| 311 | com2 | g4 | 10 | 63 |
| 316 | com2 | g3 | 10 | 63 |
| 321 | com14 | g2 | 60 | 65 |
| 326 | com14 | g3 | 60 | 65 |
| 331 | com18 | g2 | 200 | 200 |

### Primaria 1-3 (123)
| ID | Componente | Grupo | Peso Mín (g) | Peso Máx (g) |
|-----|------------|-------|--------------|--------------|
| 206 | com11 | g3 | 200 | 200 |
| 207 | com12 | g2 | 100 | null |
| 208 | com13 | g4 | 12 | 40 |
| 209 | com3 | g1 | 12 | 60 |
| 210 | com4 | g2 | 100 | 0 |
| 227 | com5 | g6 | 5 | 7 |
| 312 | com2 | g4 | 20 | 78 |
| 317 | com2 | g3 | 20 | 78 |
| 322 | com14 | g2 | 60 | 65 |
| 327 | com14 | g3 | 60 | 65 |
| 332 | com18 | g2 | 200 | 200 |

### Primaria 4-5 (45)
| ID | Componente | Grupo | Peso Mín (g) | Peso Máx (g) |
|-----|------------|-------|--------------|--------------|
| 211 | com11 | g3 | 200 | 200 |
| 212 | com12 | g2 | 120 | null |
| 213 | com13 | g4 | 13 | 50 |
| 214 | com3 | g1 | 24 | 70 |
| 215 | com4 | g2 | 120 | 0 |
| 228 | com5 | g6 | 5 | 7 |
| 313 | com2 | g4 | 30 | 110 |
| 318 | com2 | g3 | 30 | 110 |
| 323 | com14 | g2 | 60 | 65 |
| 328 | com14 | g3 | 60 | 65 |
| 333 | com18 | g2 | 200 | 200 |

### Secundaria (6789)
| ID | Componente | Grupo | Peso Mín (g) | Peso Máx (g) |
|-----|------------|-------|--------------|--------------|
| 216 | com11 | g3 | 200 | 200 |
| 217 | com12 | g2 | 120 | null |
| 218 | com13 | g4 | 13 | 50 |
| 219 | com3 | g1 | 32 | 95 |
| 220 | com4 | g2 | 120 | 0 |
| 229 | com5 | g6 | 8 | 10 |
| 314 | com2 | g4 | 35 | 140 |
| 319 | com2 | g3 | 35 | 140 |
| 324 | com14 | g2 | 60 | 65 |
| 329 | com14 | g3 | 60 | 65 |
| 334 | com18 | g2 | 200 | 200 |

### Media Ciclo Complementario (1011)
| ID | Componente | Grupo | Peso Mín (g) | Peso Máx (g) |
|-----|------------|-------|--------------|--------------|
| 221 | com11 | g3 | 200 | 200 |
| 222 | com12 | g2 | 120 | null |
| 223 | com13 | g4 | 13 | 50 |
| 224 | com3 | g1 | 32 | 120 |
| 225 | com4 | g2 | 120 | 0 |
| 230 | com5 | g6 | 8 | 10 |
| 315 | com2 | g4 | 45 | 172 |
| 320 | com2 | g3 | 45 | 172 |
| 325 | com14 | g2 | 60 | 65 |
| 330 | com14 | g3 | 60 | 65 |
| 335 | com18 | g2 | 200 | 200 |

---

## 5. Valores de Adecuación Porcentual (nutricion_adecuacion_total_porc)

| ID Adecuación | Nivel Escolar | Calorías % | Proteína % | Grasa % | CHO % | Calcio % | Hierro % | Sodio % |
|---------------|---------------|------------|------------|---------|-------|----------|----------|---------|
| adp020511100 | 100 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |
| adp020511123 | 123 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |
| adp02051145 | 45 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |
| adp0205116789 | 6789 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |
| adp0205111011 | 1011 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |

---

## 6. Valores de Referencia Diarios (nutricion_recomendacion_diaria_por_grado_mod)

| Nivel Escolar | Calorías (kcal) | Proteína (g) | Grasa (g) | CHO (g) | Calcio (mg) | Hierro (mg) | Sodio (mg) |
|---------------|-----------------|--------------|-----------|---------|-------------|------------|------------|
| Preescolar (100) | 1300.0 | 45.5 | 43.3 | 182.0 | 700.0 | 5.6 | 1133.0 |
| Primaria 1-3 (123) | 1629.0 | 57.0 | 54.3 | 228.1 | 800.0 | 6.2 | 1200.0 |
| Primaria 4-5 (45) | 1994.0 | 69.8 | 66.5 | 279.2 | 1100.0 | 8.7 | 1500.0 |
| Secundaria (6789) | 2491.0 | 87.2 | 83.0 | 348.7 | 1100.0 | 9.5 | 1500.0 |
| Media (1011) | 2900.0 | 101.5 | 96.7 | 406.0 | 1100.0 | 11.8 | 1500.0 |

---

## 7. Comandos SQL Completos para pgAdmin

### 7.1 Eliminar datos existentes de la modalidad 020511 (si necesitas resetear)

```sql
-- Eliminar rangos
DELETE FROM public.nutricion_minuta_patron_rangos WHERE id_modalidad = '020511';

-- Eliminar valores de adecuación
DELETE FROM public.nutricion_adecuacion_total_porc WHERE id_modalidad = '020511';

-- Eliminar recomendaciones diarias
DELETE FROM public.nutricion_recomendacion_diaria_por_grado_mod WHERE id_modalidades = '020511';
```

### 7.2 Insertar TODOS los rangos de peso neto (nutricion_minuta_patron_rangos)

```sql
INSERT INTO public.nutricion_minuta_patron_rangos
(id, id_modalidad, id_grado_escolar_uapa, id_componente, id_grupo_alimentos, peso_neto_minimo, peso_neto_maximo)
VALUES
-- Preescolar (100)
(201, '020511', '100', 'com11', 'g3', 180, 180),
(202, '020511', '100', 'com12', 'g2', 100, NULL),
(203, '020511', '100', 'com13', 'g4', 12, 40),
(204, '020511', '100', 'com3', 'g1', 12, 40),
(205, '020511', '100', 'com4', 'g2', 100, 0),
(226, '020511', '100', 'com5', 'g6', 5, 7),
(311, '020511', '100', 'com2', 'g4', 10, 63),
(316, '020511', '100', 'com2', 'g3', 10, 63),
(321, '020511', '100', 'com14', 'g2', 60, 65),
(326, '020511', '100', 'com14', 'g3', 60, 65),
(331, '020511', '100', 'com18', 'g2', 200, 200),

-- Primaria 1-3 (123)
(206, '020511', '123', 'com11', 'g3', 200, 200),
(207, '020511', '123', 'com12', 'g2', 100, NULL),
(208, '020511', '123', 'com13', 'g4', 12, 40),
(209, '020511', '123', 'com3', 'g1', 12, 60),
(210, '020511', '123', 'com4', 'g2', 100, 0),
(227, '020511', '123', 'com5', 'g6', 5, 7),
(312, '020511', '123', 'com2', 'g4', 20, 78),
(317, '020511', '123', 'com2', 'g3', 20, 78),
(322, '020511', '123', 'com14', 'g2', 60, 65),
(327, '020511', '123', 'com14', 'g3', 60, 65),
(332, '020511', '123', 'com18', 'g2', 200, 200),

-- Primaria 4-5 (45)
(211, '020511', '45', 'com11', 'g3', 200, 200),
(212, '020511', '45', 'com12', 'g2', 120, NULL),
(213, '020511', '45', 'com13', 'g4', 13, 50),
(214, '020511', '45', 'com3', 'g1', 24, 70),
(215, '020511', '45', 'com4', 'g2', 120, 0),
(228, '020511', '45', 'com5', 'g6', 5, 7),
(313, '020511', '45', 'com2', 'g4', 30, 110),
(318, '020511', '45', 'com2', 'g3', 30, 110),
(323, '020511', '45', 'com14', 'g2', 60, 65),
(328, '020511', '45', 'com14', 'g3', 60, 65),
(333, '020511', '45', 'com18', 'g2', 200, 200),

-- Secundaria (6789)
(216, '020511', '6789', 'com11', 'g3', 200, 200),
(217, '020511', '6789', 'com12', 'g2', 120, NULL),
(218, '020511', '6789', 'com13', 'g4', 13, 50),
(219, '020511', '6789', 'com3', 'g1', 32, 95),
(220, '020511', '6789', 'com4', 'g2', 120, 0),
(229, '020511', '6789', 'com5', 'g6', 8, 10),
(314, '020511', '6789', 'com2', 'g4', 35, 140),
(319, '020511', '6789', 'com2', 'g3', 35, 140),
(324, '020511', '6789', 'com14', 'g2', 60, 65),
(329, '020511', '6789', 'com14', 'g3', 60, 65),
(334, '020511', '6789', 'com18', 'g2', 200, 200),

-- Media Ciclo Complementario (1011)
(221, '020511', '1011', 'com11', 'g3', 200, 200),
(222, '020511', '1011', 'com12', 'g2', 120, NULL),
(223, '020511', '1011', 'com13', 'g4', 13, 50),
(224, '020511', '1011', 'com3', 'g1', 32, 120),
(225, '020511', '1011', 'com4', 'g2', 120, 0),
(230, '020511', '1011', 'com5', 'g6', 8, 10),
(315, '020511', '1011', 'com2', 'g4', 45, 172),
(320, '020511', '1011', 'com2', 'g3', 45, 172),
(325, '020511', '1011', 'com14', 'g2', 60, 65),
(330, '020511', '1011', 'com14', 'g3', 60, 65),
(335, '020511', '1011', 'com18', 'g2', 200, 200);
```

### 7.3 Insertar valores de adecuación porcentual (nutricion_adecuacion_total_porc)

```sql
INSERT INTO public.nutricion_adecuacion_total_porc
(id_adecuacion_porcentaje, id_modalidad, id_nivel_escolar_uapa, sodio_porc, calorias_porc, proteina_porc, grasa_porc, cho_porc, calcio_porc, hierro_porc)
VALUES
('adp020511100', '020511', '100', 20, 20, 20, 20, 20, 20, 20),
('adp020511123', '020511', '123', 20, 20, 20, 20, 20, 20, 20),
('adp02051145', '020511', '45', 20, 20, 20, 20, 20, 20, 20),
('adp0205116789', '020511', '6789', 20, 20, 20, 20, 20, 20, 20),
('adp0205111011', '020511', '1011', 20, 20, 20, 20, 20, 20, 20);
```

### 7.4 Insertar valores de referencia diarios (nutricion_recomendacion_diaria_por_grado_mod)

```sql
INSERT INTO public.nutricion_recomendacion_diaria_por_grado_mod
(id_calorias_nivel_escolar, id_modalidades, nivel_escolar_uapa, calorias_kcal, proteina_g, grasa_g, cho_g, calcio_mg, hierro_mg, sodio_mg)
VALUES
('rCAJMRI100', '020511', '100', 1300.0, 45.5, 43.3, 182.0, 700.0, 5.6, 1133.0),
('rCAJMRI12', '020511', '123', 1629.0, 57.0, 54.3, 228.1, 800.0, 6.2, 1200.0),
('rCAJMRI345', '020511', '45', 1994.0, 69.8, 66.5, 279.2, 1100.0, 8.7, 1500.0),
('rCAJMRI6789', '020511', '6789', 2491.0, 87.2, 83.0, 348.7, 1100.0, 9.5, 1500.0),
('rCAJMRI1011', '020511', '1011', 2900.0, 101.5, 96.7, 406.0, 1100.0, 11.8, 1500.0);
```

---

## 8. JSON de Referencia

```json
{
  "modalidad_id": "020511",
  "programa_id": 15,
  "rangos_grados": [
    {"id": "100", "nombre": "Preescolar"},
    {"id": "123", "nombre": "Primaria 1, 2, 3"},
    {"id": "45", "nombre": "Primaria 4, 5"},
    {"id": "6789", "nombre": "Secundaria"},
    {"id": "1011", "nombre": "Media ciclo complementario"}
  ],
  "componentes": [
    {"id": "com2", "nombre": "Alimento proteico"},
    {"id": "com3", "nombre": "Cereal acompañante"},
    {"id": "com4", "nombre": "Fruta"},
    {"id": "com5", "nombre": "Azúcares"},
    {"id": "com11", "nombre": "Leche y productos lácteos"},
    {"id": "com12", "nombre": "Frutas"},
    {"id": "com13", "nombre": "Postre"},
    {"id": "com14", "nombre": "Bebida"},
    {"id": "com18", "nombre": "(Nuevo)"}
  ],
  "grupos_alimentos": [
    {"id": "g1", "nombre": "Grupo I. Cereales, raíces, tubérculos y plátanos"},
    {"id": "g2", "nombre": "Grupo II. Fruta y verduras"},
    {"id": "g3", "nombre": "Grupo III. Leche y productos lácteos"},
    {"id": "g4", "nombre": "Grupo IV. Carnes, huevos, leguminosas secas, frutos secos y semillas"},
    {"id": "g6", "nombre": "Grupo VI. Azúcares"}
  ],
  "rangos_peso_neto": [
    {"id": 201, "grado": "100", "componente": "com11", "grupo": "g3", "min": 180, "max": 180},
    {"id": 202, "grado": "100", "componente": "com12", "grupo": "g2", "min": 100, "max": null},
    {"id": 203, "grado": "100", "componente": "com13", "grupo": "g4", "min": 12, "max": 40},
    {"id": 204, "grado": "100", "componente": "com3", "grupo": "g1", "min": 12, "max": 40},
    {"id": 205, "grado": "100", "componente": "com4", "grupo": "g2", "min": 100, "max": 0},
    {"id": 226, "grado": "100", "componente": "com5", "grupo": "g6", "min": 5, "max": 7},
    {"id": 311, "grado": "100", "componente": "com2", "grupo": "g4", "min": 10, "max": 63},
    {"id": 316, "grado": "100", "componente": "com2", "grupo": "g3", "min": 10, "max": 63},
    {"id": 321, "grado": "100", "componente": "com14", "grupo": "g2", "min": 60, "max": 65},
    {"id": 326, "grado": "100", "componente": "com14", "grupo": "g3", "min": 60, "max": 65},
    {"id": 331, "grado": "100", "componente": "com18", "grupo": "g2", "min": 200, "max": 200},
    {"id": 206, "grado": "123", "componente": "com11", "grupo": "g3", "min": 200, "max": 200},
    {"id": 207, "grado": "123", "componente": "com12", "grupo": "g2", "min": 100, "max": null},
    {"id": 208, "grado": "123", "componente": "com13", "grupo": "g4", "min": 12, "max": 40},
    {"id": 209, "grado": "123", "componente": "com3", "grupo": "g1", "min": 12, "max": 60},
    {"id": 210, "grado": "123", "componente": "com4", "grupo": "g2", "min": 100, "max": 0},
    {"id": 227, "grado": "123", "componente": "com5", "grupo": "g6", "min": 5, "max": 7},
    {"id": 312, "grado": "123", "componente": "com2", "grupo": "g4", "min": 20, "max": 78},
    {"id": 317, "grado": "123", "componente": "com2", "grupo": "g3", "min": 20, "max": 78},
    {"id": 322, "grado": "123", "componente": "com14", "grupo": "g2", "min": 60, "max": 65},
    {"id": 327, "grado": "123", "componente": "com14", "grupo": "g3", "min": 60, "max": 65},
    {"id": 332, "grado": "123", "componente": "com18", "grupo": "g2", "min": 200, "max": 200},
    {"id": 211, "grado": "45", "componente": "com11", "grupo": "g3", "min": 200, "max": 200},
    {"id": 212, "grado": "45", "componente": "com12", "grupo": "g2", "min": 120, "max": null},
    {"id": 213, "grado": "45", "componente": "com13", "grupo": "g4", "min": 13, "max": 50},
    {"id": 214, "grado": "45", "componente": "com3", "grupo": "g1", "min": 24, "max": 70},
    {"id": 215, "grado": "45", "componente": "com4", "grupo": "g2", "min": 120, "max": 0},
    {"id": 228, "grado": "45", "componente": "com5", "grupo": "g6", "min": 5, "max": 7},
    {"id": 313, "grado": "45", "componente": "com2", "grupo": "g4", "min": 30, "max": 110},
    {"id": 318, "grado": "45", "componente": "com2", "grupo": "g3", "min": 30, "max": 110},
    {"id": 323, "grado": "45", "componente": "com14", "grupo": "g2", "min": 60, "max": 65},
    {"id": 328, "grado": "45", "componente": "com14", "grupo": "g3", "min": 60, "max": 65},
    {"id": 333, "grado": "45", "componente": "com18", "grupo": "g2", "min": 200, "max": 200},
    {"id": 216, "grado": "6789", "componente": "com11", "grupo": "g3", "min": 200, "max": 200},
    {"id": 217, "grado": "6789", "componente": "com12", "grupo": "g2", "min": 120, "max": null},
    {"id": 218, "grado": "6789", "componente": "com13", "grupo": "g4", "min": 13, "max": 50},
    {"id": 219, "grado": "6789", "componente": "com3", "grupo": "g1", "min": 32, "max": 95},
    {"id": 220, "grado": "6789", "componente": "com4", "grupo": "g2", "min": 120, "max": 0},
    {"id": 229, "grado": "6789", "componente": "com5", "grupo": "g6", "min": 8, "max": 10},
    {"id": 314, "grado": "6789", "componente": "com2", "grupo": "g4", "min": 35, "max": 140},
    {"id": 319, "grado": "6789", "componente": "com2", "grupo": "g3", "min": 35, "max": 140},
    {"id": 324, "grado": "6789", "componente": "com14", "grupo": "g2", "min": 60, "max": 65},
    {"id": 329, "grado": "6789", "componente": "com14", "grupo": "g3", "min": 60, "max": 65},
    {"id": 334, "grado": "6789", "componente": "com18", "grupo": "g2", "min": 200, "max": 200},
    {"id": 221, "grado": "1011", "componente": "com11", "grupo": "g3", "min": 200, "max": 200},
    {"id": 222, "grado": "1011", "componente": "com12", "grupo": "g2", "min": 120, "max": null},
    {"id": 223, "grado": "1011", "componente": "com13", "grupo": "g4", "min": 13, "max": 50},
    {"id": 224, "grado": "1011", "componente": "com3", "grupo": "g1", "min": 32, "max": 120},
    {"id": 225, "grado": "1011", "componente": "com4", "grupo": "g2", "min": 120, "max": 0},
    {"id": 230, "grado": "1011", "componente": "com5", "grupo": "g6", "min": 8, "max": 10},
    {"id": 315, "grado": "1011", "componente": "com2", "grupo": "g4", "min": 45, "max": 172},
    {"id": 320, "grado": "1011", "componente": "com2", "grupo": "g3", "min": 45, "max": 172},
    {"id": 325, "grado": "1011", "componente": "com14", "grupo": "g2", "min": 60, "max": 65},
    {"id": 330, "grado": "1011", "componente": "com14", "grupo": "g3", "min": 60, "max": 65},
    {"id": 335, "grado": "1011", "componente": "com18", "grupo": "g2", "min": 200, "max": 200}
  ],
  "adecuacion_porcentual": [
    {"id": "adp020511100", "grado": "100", "calorias": 20, "proteina": 20, "grasa": 20, "cho": 20, "calcio": 20, "hierro": 20, "sodio": 20},
    {"id": "adp020511123", "grado": "123", "calorias": 20, "proteina": 20, "grasa": 20, "cho": 20, "calcio": 20, "hierro": 20, "sodio": 20},
    {"id": "adp02051145", "grado": "45", "calorias": 20, "proteina": 20, "grasa": 20, "cho": 20, "calcio": 20, "hierro": 20, "sodio": 20},
    {"id": "adp0205116789", "grado": "6789", "calorias": 20, "proteina": 20, "grasa": 20, "cho": 20, "calcio": 20, "hierro": 20, "sodio": 20},
    {"id": "adp0205111011", "grado": "1011", "calorias": 20, "proteina": 20, "grasa": 20, "cho": 20, "calcio": 20, "hierro": 20, "sodio": 20}
  ],
  "requerimientos_diarios": [
    {
      "nivel_escolar": "100",
      "calorias_kcal": 1300.0,
      "proteina_g": 45.5,
      "grasa_g": 43.3,
      "cho_g": 182.0,
      "calcio_mg": 700.0,
      "hierro_mg": 5.6,
      "sodio_mg": 1133.0
    },
    {
      "nivel_escolar": "123",
      "calorias_kcal": 1629.0,
      "proteina_g": 57.0,
      "grasa_g": 54.3,
      "cho_g": 228.1,
      "calcio_mg": 800.0,
      "hierro_mg": 6.2,
      "sodio_mg": 1200.0
    },
    {
      "nivel_escolar": "45",
      "calorias_kcal": 1994.0,
      "proteina_g": 69.8,
      "grasa_g": 66.5,
      "cho_g": 279.2,
      "calcio_mg": 1100.0,
      "hierro_mg": 8.7,
      "sodio_mg": 1500.0
    },
    {
      "nivel_escolar": "6789",
      "calorias_kcal": 2491.0,
      "proteina_g": 87.2,
      "grasa_g": 83.0,
      "cho_g": 348.7,
      "calcio_mg": 1100.0,
      "hierro_mg": 9.5,
      "sodio_mg": 1500.0
    },
    {
      "nivel_escolar": "1011",
      "calorias_kcal": 2900.0,
      "proteina_g": 101.5,
      "grasa_g": 96.7,
      "cho_g": 406.0,
      "calcio_mg": 1100.0,
      "hierro_mg": 11.8,
      "sodio_mg": 1500.0
    }
  ]
}
```
