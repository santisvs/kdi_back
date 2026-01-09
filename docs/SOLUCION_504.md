# Solución: Error 504 Gateway Timeout en /auth/register

## Problema

El endpoint `/auth/register` devuelve un 504 Gateway Timeout, mientras que `/health` funciona correctamente.

## Causa Probable

El 504 indica que la aplicación está intentando conectarse a la base de datos pero:
1. Las variables de entorno de la base de datos no están configuradas en Elastic Beanstalk
2. O la conexión a RDS está fallando/bloqueando

## Solución

### Paso 1: Verificar Variables de Entorno en Elastic Beanstalk

Las variables de entorno de la base de datos **DEBEN** estar configuradas en Elastic Beanstalk.

#### Opción A: Desde la Consola Web de AWS

1. Ve a **AWS Console** → **Elastic Beanstalk** → Tu entorno (`kdi-back-prod` o similar)
2. Click en **Configuration** (Configuración)
3. En el panel izquierdo, click en **Software** (Software)
4. Scroll down hasta **Environment properties** (Propiedades del entorno)
5. Agrega o verifica estas variables:

```
DB_HOST=tu-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_NAME=kdi_production
DB_USER=kdi_admin
DB_PASSWORD=tu_contraseña_segura
```

6. Click en **Apply** (Aplicar)
7. Espera a que el entorno se actualice (puede tardar varios minutos)

#### Opción B: Desde EB CLI

```powershell
eb setenv `
  DB_HOST=tu-endpoint.rds.amazonaws.com `
  DB_PORT=5432 `
  DB_NAME=kdi_production `
  DB_USER=kdi_admin `
  DB_PASSWORD=tu_contraseña_segura
```

**⚠️ IMPORTANTE**: Reemplaza los valores con los reales de tu RDS:
- `DB_HOST`: El endpoint de tu instancia RDS (ej: `kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com`)
- `DB_NAME`: El nombre de la base de datos (ej: `kdi_production`)
- `DB_USER`: El usuario maestro de RDS
- `DB_PASSWORD`: La contraseña del usuario maestro

### Paso 2: Obtener los Datos de Conexión de RDS

Si no tienes los datos de conexión:

1. Ve a **AWS Console** → **RDS** → **Databases**
2. Selecciona tu instancia de base de datos
3. En **Connectivity & security**, copia el **Endpoint**
4. En la pestaña **Configuration**, encuentra el **DB name** (nombre de la base de datos)
5. El usuario y contraseña son los que configuraste al crear la instancia RDS

### Paso 3: Configurar Security Groups (MUY IMPORTANTE)

**Este es el paso más crítico.** El Security Group de RDS debe permitir conexiones desde el Security Group de Elastic Beanstalk.

#### Paso 3.1: Encontrar el Security Group de Elastic Beanstalk

1. Ve a **AWS Console** → **Elastic Beanstalk** → Tu entorno (ej: `kdi-back-prod`)
2. Click en **Configuration** (Configuración)
3. En el panel izquierdo, click en **Instances** (Instancias)
4. Busca la sección **Security** → **EC2 security groups**
5. **Copia el ID del security group** (ej: `sg-0a1b2c3d4e5f6g7h8`)
   - Puede haber uno o varios, copia el principal (generalmente el que tiene el nombre más largo)

**Alternativa: Desde EC2 Console**
1. Ve a **EC2** → **Instances**
2. Busca las instancias que pertenecen a tu entorno EB (filtra por "Elastic Beanstalk")
3. Selecciona una instancia
4. En la pestaña **Security**, verás el **Security groups** → **Copia el ID**

#### Paso 3.2: Configurar el Security Group de RDS

1. Ve a **AWS Console** → **RDS** → **Databases**
2. Selecciona tu instancia de RDS
3. En la pestaña **Connectivity & security**, encuentra **VPC security groups**
4. **Copia el ID del security group** de RDS (ej: `sg-9a8b7c6d5e4f3g2h1`)
5. Click en el ID del security group (se abrirá en una nueva pestaña)

**En la ventana del Security Group:**
1. Ve a la pestaña **Inbound rules** (Reglas de entrada)
2. Click en **Edit inbound rules** (Editar reglas de entrada)

**⚠️ IMPORTANTE**: Si ya existe una regla para PostgreSQL (puerto 5432) usando CIDR (IP ranges), NO la modifiques. Debes crear una NUEVA regla.

3. Scroll hacia abajo hasta ver todas las reglas existentes
4. Si ya existe una regla para PostgreSQL/5432:
   - **NO la elimines ni la modifiques**
   - Deja esa regla como está (puede ser para acceso desde tu IP o desde 0.0.0.0/0)
   - **Crea una regla NUEVA** (ver paso siguiente)
   
   Si NO existe ninguna regla para 5432:
   - Procede directamente al paso siguiente

5. Click en **Add rule** (Agregar regla) para crear una NUEVA regla
6. Configura la nueva regla:
   - **Type**: Selecciona **PostgreSQL** de la lista desplegable
     - Si PostgreSQL no está en la lista, selecciona **Custom TCP**
   - **Protocol**: TCP (se llena automáticamente si seleccionaste PostgreSQL)
   - **Port range**: `5432` (se llena automáticamente si seleccionaste PostgreSQL)
   - **Source**: 
     - **IMPORTANTE**: En el dropdown de "Source", NO selecciones "Anywhere-IPv4" ni "Custom" con IP
     - En el campo de texto, selecciona la opción que dice algo como **"Security Group ID"** o busca en el dropdown
     - O simplemente **escribe directamente el ID del Security Group** (ej: `sg-0a1b2c3d4e5f6g7h8`)
     - AWS debería autocompletar y mostrar el nombre del Security Group
   - **Description**: "Permitir conexiones desde Elastic Beanstalk" (opcional pero recomendado)
7. Click en **Save rules** (Guardar reglas)

**Si aún te da error**, prueba esta alternativa:
- En lugar de escribir el ID directamente, usa el selector de Security Group:
  - Click en el campo "Source"
  - Debería aparecer un dropdown o selector
  - Busca y selecciona el Security Group de Elastic Beanstalk por su nombre o ID
  - Si no aparece, intenta escribir `sg-` seguido del ID completo

**Solución alternativa si el error persiste**:
Si ya tienes una regla con `0.0.0.0/0` (cualquier IP), técnicamente ya debería funcionar, pero es menos seguro. Si quieres ser más específico:
1. Elimina la regla existente con `0.0.0.0/0` (solo si es seguro hacerlo)
2. Crea una nueva regla con el Security Group de EB

**⚠️ IMPORTANTE**: 
- NO uses `0.0.0.0/0` como Source (eso permite acceso desde cualquier lugar)
- Debes usar el ID específico del Security Group de Elastic Beanstalk
- Esto es más seguro y es la práctica recomendada

#### Paso 3.3: Verificar que están en la misma VPC (Opcional pero recomendado)

Para que funcione correctamente, es mejor que RDS y Elastic Beanstalk estén en la misma VPC:

1. **Verificar VPC de RDS**:
   - Ve a RDS → Tu instancia → Pestaña **Connectivity & security**
   - Anota el **VPC ID** (ej: `vpc-0a1b2c3d4e5f6g7h8`)

2. **Verificar VPC de Elastic Beanstalk**:
   - Ve a Elastic Beanstalk → Tu entorno → **Configuration** → **Network**
   - Anota el **VPC ID**

3. **Si son diferentes**:
   - Lo ideal es que estén en la misma VPC
   - Si no es posible, deberás configurar VPC Peering (más complejo)
   - Por ahora, si los Security Groups están bien configurados, debería funcionar

#### Paso 3.4: Verificar Configuración Completa

Después de configurar el Security Group, verifica que tengas:

✅ **Variables de entorno configuradas** en Elastic Beanstalk:
- `DB_HOST` = endpoint de RDS
- `DB_PORT` = 5432
- `DB_NAME` = nombre de la base de datos
- `DB_USER` = usuario de RDS
- `DB_PASSWORD` = contraseña de RDS

✅ **Security Group de RDS** con regla de entrada que permite:
- Type: PostgreSQL (puerto 5432)
- Source: Security Group de Elastic Beanstalk

✅ **RDS está disponible**:
- Estado: Available
- Endpoint: accesible

### Paso 4: Verificar Logs después de Configurar

Después de configurar las variables de entorno:

```powershell
# Ver logs en tiempo real
eb logs --stream

# O ver los últimos logs
eb logs
```

Busca mensajes como:
- ✅ `Pool de conexiones a PostgreSQL creado exitosamente`
- ✅ `✓ PostGIS disponible`
- ❌ `Error al crear el pool de conexiones`
- ❌ `Error al inicializar la base de datos`

### Paso 5: Verificar que la Aplicación se Inicia Correctamente

Después de configurar las variables de entorno y que el entorno se actualice:

1. Verifica el estado:
   ```powershell
   eb status
   ```

2. Verifica los logs para asegurarte de que la aplicación inicia correctamente:
   ```powershell
   eb logs
   ```

3. Prueba el endpoint de health (debería funcionar):
   ```powershell
   curl https://tu-entorno.elasticbeanstalk.com/health
   ```

4. Prueba el endpoint de register:
   ```powershell
   curl -X POST https://tu-entorno.elasticbeanstalk.com/auth/register `
     -H "Content-Type: application/json" `
     -d '{"email":"test@example.com","username":"testuser","password":"password123"}'
   ```

## Cambios Realizados en el Código

Se modificó `create_app()` para que:
1. No bloquee el inicio de la aplicación si `init_database()` falla
2. Muestre mensajes de advertencia más claros
3. Permita que la aplicación inicie aunque la BD no esté disponible inicialmente

Esto permite que la aplicación se inicie y muestre errores más claros cuando se intenta usar la BD.

## Verificación Rápida

### Opción 1: Script de Verificación Automática

He creado un script que verifica automáticamente toda la configuración:

```powershell
.\scripts\verificar_conexion_rds.ps1
```

Este script verifica:
- ✅ Security Groups configurados correctamente
- ✅ Variables de entorno en Elastic Beanstalk
- ✅ Conectividad de red

### Opción 2: Verificación Manual

Ejecuta estos comandos para verificar la configuración:

```powershell
# Ver las variables de entorno configuradas
eb printenv

# Ver el estado del entorno
eb status

# Ver logs recientes
eb logs --all
```

### Opción 3: Verificar desde la Consola Web

1. **Verificar Security Group de RDS**:
   - EC2 → Security Groups → Selecciona el SG de RDS
   - Inbound rules → Debe permitir PostgreSQL (5432) desde el SG de EB

2. **Verificar Variables de Entorno**:
   - Elastic Beanstalk → Tu entorno → Configuration → Software
   - Deben estar todas las variables DB_*

## Si el Problema Persiste

Si después de configurar las variables de entorno el problema persiste:

1. **Verifica que RDS esté disponible**:
   - Ve a RDS → Tu instancia
   - Verifica que el estado sea **Available**

2. **Verifica conectividad desde Elastic Beanstalk**:
   - Puedes SSH al entorno EB (si está habilitado)
   - Intenta conectarte manualmente a RDS usando `psql` o `python`

3. **Verifica los logs detallados**:
   ```powershell
   eb logs --all
   ```
   Busca errores relacionados con la conexión a PostgreSQL

4. **Verifica que PostGIS esté instalado en RDS**:
   - Conecta a RDS usando DBeaver o psql
   - Ejecuta: `SELECT PostGIS_version();`
   - Si no está instalado, ejecuta: `CREATE EXTENSION IF NOT EXISTS postgis;`

## Notas Adicionales

- Las variables de entorno en Elastic Beanstalk tienen prioridad sobre cualquier configuración local
- Después de cambiar variables de entorno, el entorno se reinicia automáticamente
- El reinicio puede tardar 2-5 minutos
- Usa `eb logs --stream` para ver los logs en tiempo real durante el reinicio

