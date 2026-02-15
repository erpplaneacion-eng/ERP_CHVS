# 🚂 Guía de Deploy en Railway - ERP CHVS

Esta guía te ayudará a desplegar tu aplicación ERP_CHVS en Railway paso a paso.

## 📋 Prerequisitos

- ✅ Cuenta de Railway ([railway.app](https://railway.app))
- ✅ Cuenta de GitHub (para conectar tu repositorio)
- ✅ Tu código subido a GitHub
- ✅ Variables de entorno configuradas

## 🔐 Seguridad IMPORTANTE

### ⚠️ NUNCA subas tu archivo `.env` a GitHub

El archivo `.env` contiene credenciales sensibles y ya está en `.gitignore`. Si accidentalmente lo subiste:

```bash
# Eliminar del historial de git
git rm --cached erp_chvs/.env
git commit -m "Remove .env file from repository"
git push
```

### 🔑 Rotar claves comprometidas

Si tus API keys fueron expuestas, **rótelas inmediatamente**:

1. **Gemini API Key**: Generar nueva en [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **LandingAI Key**: Contactar soporte de LandingAI
3. **Database Password**: Regenerar en Railway

## 🚀 Paso 1: Preparar tu Repositorio

### 1.1 Verificar archivos críticos

Asegúrate de que estos archivos existen en tu repositorio:

```bash
# En la raíz del proyecto (ERP_CHVS/)
✅ .gitignore          # Excluye .env y archivos sensibles
✅ runtime.txt         # Especifica Python 3.13.1
✅ Procfile            # Comandos de inicio para Railway
✅ railway.toml        # Configuración de Railway
✅ CLAUDE.md           # Documentación del proyecto

# En erp_chvs/
✅ requirements.txt    # Dependencias Python (con gunicorn y whitenoise)
✅ .env.example        # Plantilla de variables de entorno (SIN credenciales)
```

### 1.2 Verificar que .env NO esté en git

```bash
git status
# NO debe aparecer .env en la lista

# Si aparece, eliminarlo:
git rm --cached erp_chvs/.env
git commit -m "Remove sensitive .env file"
```

### 1.3 Hacer commit y push

```bash
git add .
git commit -m "Preparar aplicación para deploy en Railway"
git push origin master
```

## 🛤️ Paso 2: Crear Proyecto en Railway

### 2.1 Iniciar sesión en Railway

1. Ve a [railway.app](https://railway.app)
2. Inicia sesión con GitHub
3. Click en **"New Project"**

### 2.2 Conectar tu repositorio

1. Selecciona **"Deploy from GitHub repo"**
2. Busca y selecciona tu repositorio `ERP_CHVS`
3. Railway detectará automáticamente que es una aplicación Django

### 2.3 Crear base de datos PostgreSQL

1. En tu proyecto de Railway, click **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway creará automáticamente una base de datos
3. Las credenciales se configuran automáticamente en variables de entorno

## ⚙️ Paso 3: Configurar Variables de Entorno

### 3.1 En Railway, ir a Variables

1. Click en tu servicio web
2. Ve a la pestaña **"Variables"**
3. Agrega las siguientes variables:

### 3.2 Variables Requeridas

```bash
# Django Core
DJANGO_SECRET_KEY=<generar-nueva-clave-secreta>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-app.up.railway.app,*.railway.app

# Base de datos (Railway las provee automáticamente, pero puedes sobrescribirlas)
# DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT ya están configuradas

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS=https://tu-app.up.railway.app

# Gemini API (IA Generativa)
GEMINI_API_KEY=tu-nueva-api-key-aqui

# LandingAI (Opcional - solo si usas OCR/Visión)
# VISION_AGENT_API_KEY=tu-api-key
# LANDINGAI_ENVIRONMENT=production
# USE_LANDINGAI_OCR=False
```

### 3.3 Generar Django Secret Key

```bash
# Opción 1: Usar Python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Opción 2: Usar OpenSSL
openssl rand -base64 64
```

### 3.4 Actualizar DJANGO_ALLOWED_HOSTS

Después del primer deploy, Railway te dará un dominio como `tu-app.up.railway.app`. Actualiza:

```bash
DJANGO_ALLOWED_HOSTS=tu-app.up.railway.app,*.railway.app
CSRF_TRUSTED_ORIGINS=https://tu-app.up.railway.app
```

## 🏗️ Paso 4: Deploy

### 4.1 Iniciar Deploy

Railway iniciará automáticamente el deploy cuando detecte cambios en `master`.

### 4.2 Monitorear el Deploy

1. Ve a la pestaña **"Deployments"**
2. Click en el deploy activo para ver logs en tiempo real
3. Espera a ver: `✅ Deploy successful`

### 4.3 Verificar Build

El build debe ejecutar:
```bash
✅ Installing dependencies from requirements.txt
✅ Running collectstatic
✅ Running migrations
✅ Starting gunicorn server
```

## ✅ Paso 5: Verificar que todo funciona

### 5.1 Acceder a tu aplicación

1. Click en **"View Deployment"** o visita `https://tu-app.up.railway.app`
2. Deberías ver la página de inicio de ERP_CHVS

### 5.2 Acceder al Admin de Django

1. Ve a `https://tu-app.up.railway.app/admin/`
2. **IMPORTANTE**: Si no tienes superusuario, créalo desde Railway CLI:

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Iniciar sesión
railway login

# Conectar a tu proyecto
railway link

# Ejecutar shell de Django
railway run python erp_chvs/manage.py createsuperuser
```

### 5.3 Probar funcionalidades

- ✅ Login/Logout
- ✅ Dashboard
- ✅ Módulo Principal (maestros)
- ✅ Módulo Nutrición
- ✅ Módulo Planeación
- ✅ Módulo Facturación

## 🐛 Solución de Problemas

### Error: "Bad Request (400)"

**Causa**: `ALLOWED_HOSTS` no incluye el dominio de Railway

**Solución**:
```bash
# Actualizar variable en Railway:
DJANGO_ALLOWED_HOSTS=tu-app.up.railway.app,*.railway.app
```

### Error: "CSRF verification failed"

**Causa**: `CSRF_TRUSTED_ORIGINS` no configurado

**Solución**:
```bash
# Agregar en Railway:
CSRF_TRUSTED_ORIGINS=https://tu-app.up.railway.app
```

### Error: "No module named 'gunicorn'"

**Causa**: `requirements.txt` no tiene gunicorn

**Solución**:
```bash
# Ya está en tu requirements.txt actualizado
# Si persiste, forzar reinstalación:
railway run pip install -r erp_chvs/requirements.txt --force-reinstall
```

### Error: "Static files not found (404)"

**Causa**: `collectstatic` no se ejecutó correctamente

**Solución**:
```bash
# Ejecutar manualmente desde Railway CLI:
railway run python erp_chvs/manage.py collectstatic --noinput
```

### Error de conexión a base de datos

**Causa**: Variables de DB mal configuradas

**Solución**:
1. Verificar que el servicio PostgreSQL esté activo
2. Railway provee automáticamente: `DATABASE_URL`
3. Si usas variables individuales, verificar que coincidan con las de Railway

### Ver Logs en tiempo real

```bash
# Usando Railway CLI
railway logs

# O en la interfaz web
# Click en "Deployments" → Click en deploy activo → Ver logs
```

## 📊 Monitoreo y Mantenimiento

### Ver métricas

1. En Railway, ve a la pestaña **"Metrics"**
2. Monitorea:
   - CPU usage
   - Memory usage
   - Network traffic
   - Response times

### Configurar Healthcheck

Ya está configurado en `railway.toml`:
```toml
[healthcheck]
path = "/"
timeout = 100
interval = 60
```

### Backups de Base de Datos

Railway hace backups automáticos, pero puedes hacer backups manuales:

```bash
# Desde Railway CLI
railway run python erp_chvs/manage.py dumpdata > backup_$(date +%Y%m%d).json

# Descargar backup
railway run cat backup_*.json > local_backup.json
```

## 🔄 Actualizar la Aplicación

### Cambios de código

```bash
# 1. Hacer cambios localmente
# 2. Commit
git add .
git commit -m "Descripción de cambios"

# 3. Push (Railway detecta y hace redeploy automáticamente)
git push origin master
```

### Cambios de variables de entorno

1. Ve a Railway → Variables
2. Edita o agrega variables
3. Railway reinicia automáticamente el servicio

### Ejecutar migraciones

```bash
# Las migraciones se ejecutan automáticamente en cada deploy (ver Procfile)
# Si necesitas ejecutarlas manualmente:
railway run python erp_chvs/manage.py migrate
```

## 💰 Costos Estimados

Railway ofrece:
- **$5 USD/mes** de créditos gratis (Hobby plan)
- **~$5-10 USD/mes** para aplicaciones pequeñas
- Cobra por uso real (CPU, RAM, tráfico)

### Optimizar costos

- Usar **Starter Plan** ($5/mes) si es suficiente
- Configurar **Sleep Mode** si la app no se usa 24/7
- Monitorear uso de recursos regularmente

## 📚 Recursos Adicionales

- [Documentación Railway](https://docs.railway.app)
- [Railway CLI Reference](https://docs.railway.app/develop/cli)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)

## 🆘 Soporte

Si encuentras problemas:

1. **Revisar logs**: `railway logs`
2. **Revisar este archivo**: `DEPLOY_RAILWAY.md`
3. **Consultar CLAUDE.md**: Documentación del proyecto
4. **Railway Support**: [railway.app/help](https://railway.app/help)
5. **GitHub Issues**: Reportar bugs en el repositorio

---

## ✅ Checklist Final

Antes de considerar el deploy completo:

- [ ] Aplicación accesible en URL de Railway
- [ ] Login funcionando
- [ ] Admin de Django accesible
- [ ] Archivos estáticos cargando correctamente
- [ ] Base de datos funcionando
- [ ] API de Gemini funcionando (generación de menús)
- [ ] Superusuario creado
- [ ] Variables de entorno configuradas
- [ ] `.env` NO está en GitHub
- [ ] Logs sin errores críticos
- [ ] CSRF configurado correctamente

¡Felicidades! 🎉 Tu aplicación ERP_CHVS está ahora en producción en Railway.
