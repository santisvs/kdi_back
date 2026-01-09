# Guía de Despliegue en AWS - KDI Back

Esta guía te ayudará a desplegar tu aplicación Flask en AWS usando Elastic Beanstalk y RDS PostgreSQL con PostGIS.

## Arquitectura de Despliegue

```
┌─────────────────────────────────────┐
│   AWS Elastic Beanstalk             │
│   ┌───────────────────────────────┐ │
│   │   Flask Application            │ │
│   │   (kdi_back)                   │ │
│   └───────────────────────────────┘ │
└─────────────────────────────────────┘
              │
              │ (IAM Role)
              ▼
┌─────────────────────────────────────┐
│   AWS Services                      │
│   - Bedrock (IA Agents)             │
│   - Knowledge Base                  │
└─────────────────────────────────────┘
              │
              │ (Connection String)
              ▼
┌─────────────────────────────────────┐
│   AWS RDS PostgreSQL                │
│   - PostGIS Extension               │
│   - Base de datos de golf           │
└─────────────────────────────────────┘
```

## Prerrequisitos

1. **Cuenta de AWS** con permisos para:
   - Elastic Beanstalk
   - RDS
   - IAM
   - Bedrock
   - EC2

2. **AWS CLI instalado y configurado**:
   ```powershell
   # Verificar que AWS CLI está instalado
   aws --version
   
   # Si no está instalado, instálalo:
   # Opción 1: Con pip
   pip install awscli
   
   # Opción 2: Descargar instalador desde https://aws.amazon.com/cli/
   ```
   
   **Obtener tus credenciales de AWS:**
   
   Si **NO tienes credenciales** o **no sabes dónde están**:
   
   1. **Ve a la consola de AWS**: https://console.aws.amazon.com/
   2. **Inicia sesión** con tu cuenta de AWS
   3. **Ve a IAM** → **Users** (o **Security credentials** en el menú superior derecho)
   4. **Selecciona tu usuario** (o crea uno nuevo si no tienes)
   5. **Ve a la pestaña "Security credentials"**
   6. **En "Access keys"**, click en **"Create access key"**
   7. **Selecciona el caso de uso**: "Command Line Interface (CLI)"
   8. **Descarga o copia**:
      - **Access Key ID** (ej: `AKIAIOSFODNN7EXAMPLE`)
      - **Secret Access Key** (ej: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
      - ⚠️ **IMPORTANTE**: La Secret Access Key solo se muestra UNA VEZ. Guárdala de forma segura.
   
   **Si ya tienes credenciales configuradas en tu `.env` local:**
   
   Puedes usar las mismas credenciales que tienes en tu archivo `.env`:
   ```powershell
   # Ver tu .env (si tienes las credenciales ahí)
   # Las credenciales estarán como:
   # AWS_ACCESS_KEY_ID=tu_access_key
   # AWS_SECRET_ACCESS_KEY=tu_secret_key
   ```
   
   **Configurar credenciales de AWS:**
   ```powershell
   aws configure
   ```
   
   Te pedirá:
   - **AWS Access Key ID**: Tu access key de AWS (la que obtuviste o tienes en .env)
   - **AWS Secret Access Key**: Tu secret key de AWS (la que obtuviste o tienes en .env)
   - **Default region name**: `eu-south-2` (o la región que prefieras)
   - **Default output format**: `json` (recomendado)
   
   **⚠️ IMPORTANTE**: 
   - Estas credenciales se guardan en `~/.aws/credentials` y `~/.aws/config`
   - **NO compartas** estas credenciales con nadie
   - Si las pierdes o se comprometen, elimínalas y crea nuevas desde IAM
   
   **Si ya tienes las credenciales configuradas**, puedes verificar:
   ```powershell
   aws sts get-caller-identity
   ```
   
   Esto debería mostrar tu cuenta de AWS si las credenciales están correctas.

3. **EB CLI instalado** (Requerido para desplegar):
   ```powershell
   # Instalar EB CLI
   pip install awsebcli
   
   # Verificar instalación
   eb --version
   ```
   
   **Si el comando `eb` no se reconoce después de instalarlo:**
   - Asegúrate de que Python y pip estén en tu PATH
   - Reinicia PowerShell después de la instalación
   - O usa: `python -m awsebcli` en lugar de `eb`

## Paso 1: Preparar la Base de Datos RDS

### 1.1 Crear Instancia RDS PostgreSQL

1. Ve a la consola de AWS → **RDS** → **Create database**

2. **⚠️ IMPORTANTE - Seleccionar Región:**
   - En la esquina superior derecha, asegúrate de estar en la región **eu-south-2 (España)**
   - O la región donde quieras tener tu RDS (debe coincidir con tu Knowledge Base si es posible)

3. Selecciona:
   - **Engine**: PostgreSQL
   - **Version**: 14.x o superior (recomendado 15.x)
   - **Template**: Production o Dev/Test según tu caso
   - **DB instance identifier**: `kdi-back-db`
   - **Master username**: `kdi_admin` (o el que prefieras)
   - **Master password**: Genera una contraseña segura
   - **DB instance class**: `db.t3.micro` (dev) o `db.t3.small` (producción)
   - **Storage**: 20 GB mínimo
   - **VPC**: Selecciona o crea una VPC
   - **Public access**: **Sí** (o configura VPC peering si prefieres)
   - **Security group**: Crea uno nuevo o usa existente

3. **Configuración avanzada**:
   - **Database name**: `kdi_production`
   - **Backup retention**: 7 días (producción)
   - **Enable encryption**: Sí

4. Click en **Create database**

### 1.2 Configurar Security Group

1. Ve a **EC2** → **Security Groups**
2. Encuentra el security group de tu RDS
3. Agrega regla de entrada:
   - **Type**: PostgreSQL
   - **Port**: 5432
   - **Source**: El security group de Elastic Beanstalk (lo configurarás después)

### 1.3 Instalar PostGIS en RDS

Una vez creada la base de datos:

1. Conéctate a tu instancia RDS usando un cliente PostgreSQL (DBeaver, PgAdmin4, o psql)
   - **Recomendado**: DBeaver (ver sección 1.4)
2. Ejecuta:
   ```sql
   -- Conectarte a la base de datos
   \c kdi_production
   
   -- Instalar PostGIS
   CREATE EXTENSION IF NOT EXISTS postgis;
   
   -- Verificar instalación
   SELECT PostGIS_version();
   ```

**Alternativa usando AWS CLI**:
```bash
# Instalar AWS RDS Data API (opcional)
aws rds-data execute-statement \
  --resource-arn "arn:aws:rds:REGION:ACCOUNT:cluster:CLUSTER_NAME" \
  --secret-arn "SECRET_ARN" \
  --database "kdi_production" \
  --sql "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### 1.4 Conectarse a RDS desde DBeaver (Local)

Para gestionar tu base de datos RDS desde tu ordenador usando DBeaver (recomendado), sigue estos pasos:

> **Nota**: También puedes usar PgAdmin4 u otros clientes PostgreSQL. Las instrucciones para PgAdmin4 están al final de esta sección.

#### Paso 1: Obtener tu IP Pública

Necesitas conocer tu IP pública para permitir el acceso desde tu ordenador:

**Opción A: Desde el navegador**
- Visita: https://whatismyipaddress.com/
- Anota tu dirección IPv4

**Opción B: Desde PowerShell**
```powershell
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

**Opción C: Desde CMD**
```cmd
curl https://api.ipify.org
```

⚠️ **Nota**: Si tu IP cambia (conexión dinámica), tendrás que actualizar el security group cada vez.

#### Paso 2: Configurar Security Group de RDS

1. Ve a la consola de AWS → **EC2** → **Security Groups**
2. Busca y selecciona el security group asociado a tu instancia RDS (puedes verlo en la configuración de RDS)
3. Ve a la pestaña **Inbound rules** (Reglas de entrada)
4. Click en **Edit inbound rules** (Editar reglas de entrada)
5. Click en **Add rule** (Agregar regla)
6. Configura la nueva regla:
   - **Type**: PostgreSQL
   - **Protocol**: TCP
   - **Port range**: 5432
   - **Source**: **My IP** (si está disponible) o **Custom** con tu IP pública (ej: `123.45.67.89/32`)
   - **Description**: "Acceso desde cliente PostgreSQL local"
7. Click en **Save rules** (Guardar reglas)

**Para permitir acceso desde cualquier IP (⚠️ Solo para desarrollo/testing)**:
- **Source**: `0.0.0.0/0` (NO recomendado para producción)

#### Paso 3: Obtener el Endpoint y Nombre de la Base de Datos

⚠️ **IMPORTANTE**: Distingue entre:
- **DB instance identifier**: Nombre de la instancia RDS (ej: `kdi-back-db`) - Solo para identificación en AWS
- **Database name**: Nombre de la base de datos PostgreSQL (ej: `kdi_production`) - Lo que necesitas para conectarte

1. Ve a la consola de AWS → **RDS** → **Databases**
2. Selecciona tu instancia de base de datos
3. En la sección **Connectivity & security**, copia el **Endpoint** (ej: `kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com`)
4. Anota también el **Port** (por defecto 5432)
5. **Para encontrar el nombre de la base de datos**:
   - Ve a la pestaña **Configuration**
   - Busca **DB name** o **Database name** (ej: `kdi_production`)
   - Si no aparece, es probable que sea `postgres` (base de datos por defecto) o el nombre que especificaste al crear la instancia
   - **Alternativa**: Si no recuerdas el nombre, usa `postgres` como Maintenance database (siempre existe) y luego listarás las bases de datos disponibles

#### Paso 4: Instalar DBeaver (Si no lo tienes)

1. Descarga DBeaver desde: https://dbeaver.io/download/
2. Instala DBeaver (Community Edition es gratuito)
3. Abre DBeaver

#### Paso 5: Configurar Conexión en DBeaver

1. **Crear nueva conexión**:
   - Click en el icono **New Database Connection** (🔌) en la barra superior
   - O ve a **Database** → **New Database Connection**

2. **Seleccionar PostgreSQL**:
   - En la lista de bases de datos, busca y selecciona **PostgreSQL**
   - Click en **Next**

3. **Configurar conexión**:
   - **Host**: Pega el endpoint de RDS (ej: `kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com`)
     - ⚠️ **NO uses el nombre de la instancia** (`kdi-back-db`), usa el endpoint completo
   - **Port**: `5432`
   - **Database**: 
     - Si creaste una base de datos específica: `kdi_production` (o el nombre que pusiste en "Database name" al crear RDS)
     - Si no estás seguro: usa `postgres` (base de datos por defecto que siempre existe)
     - ⚠️ **NO uses el nombre de la instancia** (`kdi-back-db`) aquí
   - **Username**: El usuario maestro que configuraste (ej: `kdi_admin`)
   - **Password**: La contraseña maestra que configuraste
   - ✅ Marca **Save password** si quieres guardar la contraseña

4. **Configurar SSL** (Recomendado para producción):
   - Ve a la pestaña **SSL**
   - Marca **Use SSL**
   - **SSL Mode**: `require` o `prefer`

5. **Probar la conexión**:
   - Click en **Test Connection**
   - Si es la primera vez, DBeaver te pedirá descargar el driver de PostgreSQL - Click en **Download**
   - Deberías ver "Connected" en verde

6. **Guardar la conexión**:
   - Click en **Finish**
   - Asigna un nombre a la conexión (ej: `KDI Back - AWS RDS`)

#### Paso 6: Verificar la Conexión

1. En el panel izquierdo **Database Navigator**, expande tu nueva conexión
2. Si la conexión es exitosa, verás:
   - **Databases** → `kdi_production` (y otras bases de datos del sistema)
   - **Schemas**
   - **Tables** (una vez que ejecutes las migraciones)

3. **Verificar PostGIS**:
   - Expande tu base de datos → **Extensions**
   - Deberías ver `postgis` en la lista
   - Si no está, ejecuta: `CREATE EXTENSION IF NOT EXISTS postgis;`

#### Paso 7: Ejecutar Migraciones desde DBeaver

Puedes ejecutar las migraciones directamente desde DBeaver:

1. Click derecho en tu base de datos (ej: `kdi_production`) → **SQL Editor** → **New SQL Script**
2. Abre el archivo de migraciones o pega el SQL
3. Selecciona el SQL que quieres ejecutar
4. Click en **Execute SQL Script** (▶️) o presiona `Ctrl+Enter`

**O usar el script de Python**:
```powershell
# Configurar variables de entorno en tu .env local
# O exportarlas temporalmente:
$env:DB_HOST="kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com"
$env:DB_PORT="5432"
$env:DB_NAME="kdi_production"
$env:DB_USER="kdi_admin"
$env:DB_PASSWORD="tu_contraseña"

# Ejecutar migraciones
python -m kdi_back.infrastructure.db.migrations create_all
```

#### Troubleshooting de Conexión DBeaver

**Error: "FATAL: database 'kdi-back-db' does not exist"**

Este error ocurre cuando confundes el **nombre de la instancia RDS** con el **nombre de la base de datos**:

1. **El problema**: Estás usando `kdi-back-db` (nombre de la instancia) como Database name
2. **La solución**:
   - **Opción A**: Si creaste una base de datos específica al crear RDS, usa ese nombre (ej: `kdi_production`)
   - **Opción B**: Si no recuerdas el nombre, usa `postgres` (base de datos por defecto)
   - **Opción C**: Para ver todas las bases de datos disponibles:
     - Conéctate usando `postgres` como Database name
     - Una vez conectado, expande **Databases** en el panel izquierdo
     - Verás todas las bases de datos disponibles

3. **Cómo encontrar el nombre correcto**:
   - Ve a AWS Console → RDS → Tu instancia → **Configuration**
   - Busca **DB name** o **Database name**
   - Si no aparece, probablemente sea `postgres` o el nombre que especificaste en "Database name" al crear la instancia

**Error: "could not connect to server"**

1. **Verifica el Security Group**:
   - Asegúrate de que tu IP esté en las reglas de entrada
   - Verifica que el puerto 5432 esté abierto

2. **Verifica el Endpoint**:
   - Asegúrate de usar el endpoint completo (ej: `kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com`)
   - ⚠️ **NO uses solo el nombre de la instancia** (`kdi-back-db`)
   - Verifica que no haya espacios extra

3. **Verifica las credenciales**:
   - Usuario y contraseña correctos
   - La base de datos existe

4. **Verifica el estado de RDS**:
   - En la consola de AWS, verifica que la instancia esté en estado **Available**

5. **Verifica tu conexión a internet**:
   - Prueba hacer ping al endpoint (puede que no responda, pero verifica que resuelva)

**Error: "timeout expired"**

1. Verifica que el Security Group permita tu IP actual
2. Si tu IP cambió, actualiza el Security Group
3. Verifica que no haya firewalls bloqueando el puerto 5432

**Error: "password authentication failed"**

1. Verifica usuario y contraseña
2. Si olvidaste la contraseña, puedes resetearla desde la consola de RDS:
   - RDS → Tu instancia → **Modify** → **Modify master password**

**Error: "Connection refused" o "Connection timeout"**

1. Verifica que el Security Group permita tu IP actual
2. Si tu IP cambió, actualiza el Security Group
3. Verifica que no haya firewalls bloqueando el puerto 5432
4. Verifica que la instancia RDS esté en estado **Available**

**Error: "Driver not found" o problemas con el driver PostgreSQL**

1. En DBeaver, ve a **Database** → **Driver Manager**
2. Busca **PostgreSQL**
3. Si no está, click en **New** y descarga el driver
4. O reinstala DBeaver para obtener los drivers por defecto

**Consejos adicionales para DBeaver:**

- **Auto-completado**: DBeaver tiene excelente auto-completado de SQL
- **Exportar/Importar datos**: Click derecho en tablas → **Export Data** / **Import Data**
- **Ver estructura**: Click derecho en tablas → **View Data** para ver los datos
- **Diagramas ER**: Click derecho en base de datos → **View Diagram** para ver relaciones

**Consejo: Usar IP estática o VPN**

Si tu IP cambia frecuentemente, considera:
- **AWS VPN**: Configurar un VPN para acceso seguro
- **Bastion Host**: Usar una instancia EC2 como intermediario
- **AWS Systems Manager Session Manager**: Para acceso seguro sin abrir puertos

### 1.5 Alternativa: Conectarse usando PgAdmin4

Si prefieres usar PgAdmin4 en lugar de DBeaver:

1. **Abrir PgAdmin4** en tu ordenador

2. **Crear nuevo servidor**:
   - Click derecho en **Servers** → **Register** → **Server...**

3. **Pestaña General**:
   - **Name**: `KDI Back - AWS RDS`
   - **Server group**: `Servers`

4. **Pestaña Connection**:
   - **Host name/address**: Endpoint de RDS (ej: `kdi-back-db.xxxxx.us-east-1.rds.amazonaws.com`)
   - **Port**: `5432`
   - **Maintenance database**: `postgres` o `kdi_production`
   - **Username**: Tu usuario maestro
   - **Password**: Tu contraseña
   - ✅ Marca **Save password**

5. **Pestaña SSL**:
   - **SSL mode**: `Require` o `Prefer`

6. Click en **Save**

**Troubleshooting PgAdmin4:**

Si encuentras el error `'ServerManager' object has no attribute 'user_info'`:
- Limpia el cache: Elimina `%APPDATA%\pgAdmin` y reinicia PgAdmin4
- O actualiza a la última versión de PgAdmin4

## Paso 2: Configurar IAM para Credenciales AWS

### 2.1 Crear IAM Role para Elastic Beanstalk

1. Ve a **IAM** → **Roles** → **Create role**

2. Selecciona **AWS service** → **Elastic Beanstalk**

3. **Selecciona el caso de uso**:
   - ✅ **Elastic Beanstalk - Compute** (Selecciona este)
     - Este rol se asigna a las instancias EC2 donde corre tu aplicación
     - Permite que tu aplicación Flask acceda a otros servicios de AWS (Bedrock, RDS, etc.)
   - ❌ **Elastic Beanstalk - Environment** (NO selecciones este)
     - Este rol es para que el servicio Elastic Beanstalk gestione recursos
     - No es necesario para tu caso de uso

4. Click en **Next**

5. **Adjunta las siguientes políticas**:
   
   **Opción A: Política completa (más fácil, menos restrictiva)**
   - `AmazonBedrockFullAccess` - Permite acceso completo a Bedrock (incluye Knowledge Bases)
   - `AmazonRDSReadOnlyAccess` (opcional, para monitoreo de RDS)
   
   **Opción B: Permisos específicos (más seguro, recomendado para producción)**
   
   Crea una política personalizada con estos permisos mínimos:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:InvokeModelWithResponseStream",
           "bedrock:Retrieve",
           "bedrock:RetrieveAndGenerate"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:GetFoundationModel",
           "bedrock:ListFoundationModels"
         ],
         "Resource": "*"
       }
     ]
   }
   ```
   
   **Permisos adicionales si tu Knowledge Base usa S3:**
   - Si tu Knowledge Base está conectada a un bucket S3, necesitas permisos de lectura:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "s3:GetObject",
       "s3:ListBucket"
     ],
     "Resource": [
       "arn:aws:s3:::tu-bucket-knowledge-base/*",
       "arn:aws:s3:::tu-bucket-knowledge-base"
     ]
   }
   ```
   
   **Permisos adicionales si tu Knowledge Base usa OpenSearch Serverless:**
   - Si tu Knowledge Base usa OpenSearch Serverless como base de datos vectorial:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "aoss:APIAccessAll"
     ],
     "Resource": "arn:aws:aoss:REGION:ACCOUNT:collection/tu-collection-id"
   }
   ```

6. **Nombre del role**: `kdi-back-eb-role` (o el nombre que prefieras)

7. **Descripción** (opcional): "Rol para instancias EC2 de Elastic Beanstalk - Acceso a Bedrock y RDS"

8. Click en **Create role**

**Nota importante**: Este rol se asignará a las instancias EC2 de tu entorno de Elastic Beanstalk. Tu aplicación Flask usará este rol para autenticarse con AWS Bedrock y otros servicios, por lo que **NO necesitas** incluir `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` en las variables de entorno si usas este rol.

### 2.1.1 Diferencia entre Roles: Knowledge Base vs Elastic Beanstalk

⚠️ **IMPORTANTE**: Hay dos roles diferentes y NO debes confundirlos:

**1. Rol de Servicio de la Knowledge Base** (Ya configurado, NO lo toques)
- Este rol es usado **internamente por AWS Bedrock** para acceder a los recursos de la Knowledge Base
- Tiene permisos como:
  - `AmazonBedrockFoundationModelPolicyForKnowledgeBase`
  - `AmazonBedrockOSSPolicyForKnowledgeBase`
- Este rol ya está asignado a tu Knowledge Base y AWS lo usa automáticamente
- **NO necesitas asignar estos permisos a tu rol de Elastic Beanstalk**

**2. Rol de IAM de Elastic Beanstalk** (El que estás configurando)
- Este rol es usado por **tu aplicación Flask** para invocar Bedrock y acceder a la Knowledge Base
- Solo necesita permisos para **invocar** Bedrock:
  - `bedrock:InvokeModel`
  - `bedrock:Retrieve` (para consultar Knowledge Base)
  - `bedrock:RetrieveAndGenerate`
- **NO necesita** los permisos que la Knowledge Base usa internamente

**Resumen:**
- ✅ Tu rol de Elastic Beanstalk solo necesita permisos para **usar** Bedrock (invocar, retrieve)
- ❌ NO necesita los permisos que la Knowledge Base usa para acceder a S3/OpenSearch (esos ya están en el rol de servicio de la KB)

### 2.1.2 Verificar permisos de Knowledge Base

Para verificar que tu Knowledge Base está accesible:

1. Ve a **AWS Console** → **Bedrock** → **Knowledge bases**
2. Selecciona tu Knowledge Base
3. Verifica la región donde está ubicada (ej: `eu-south-2`)
4. Verifica el tipo de base de datos vectorial (S3, OpenSearch Serverless, etc.)
5. Verifica que el **Rol de Servicio** de la Knowledge Base tenga los permisos correctos (esto ya debería estar configurado)

**Si tu Knowledge Base está en una región diferente a la de tu aplicación:**
- El rol IAM funciona en todas las regiones
- Solo asegúrate de configurar `AWS_KNOWLEDGE_BASE_REGION` en las variables de entorno de Elastic Beanstalk

### 2.2 Configuración Automática: IAM en AWS, Credenciales en Local

✅ **Ya está configurado automáticamente**. El código detecta si está ejecutándose en AWS Elastic Beanstalk o en tu entorno local:

**En AWS Elastic Beanstalk:**
- Detecta automáticamente el entorno usando la variable `ELASTIC_BEANSTALK_ENVIRONMENT`
- Usa el IAM Role asignado a la instancia EC2 (no requiere credenciales explícitas)
- Usa las variables de entorno de RDS configuradas en Elastic Beanstalk

**En tu entorno local:**
- Usa las credenciales del archivo `.env` (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- Usa la configuración de base de datos local (PostgreSQL local por defecto)

**Cómo funciona:**
- El archivo `settings.py` detecta automáticamente el entorno
- El helper `aws_client.py` crea clientes de boto3 que funcionan en ambos entornos
- **No necesitas cambiar nada** - funciona automáticamente

**Para verificar que funciona en local:**
1. Asegúrate de tener tu `.env` con las credenciales:
   ```
   AWS_ACCESS_KEY_ID=tu_access_key
   AWS_SECRET_ACCESS_KEY=tu_secret_key
   AWS_REGION=us-east-1
   ```

2. Ejecuta tu aplicación localmente - debería usar las credenciales del `.env`

**Para verificar que funciona en AWS:**
1. No incluyas `AWS_ACCESS_KEY_ID` ni `AWS_SECRET_ACCESS_KEY` en las variables de entorno de Elastic Beanstalk
2. Asegúrate de que el IAM Role esté asignado a tu entorno de EB
3. La aplicación usará automáticamente el IAM Role

## Paso 3: Desplegar en Elastic Beanstalk

### 3.1 Instalar EB CLI (Si no lo tienes)

Si obtienes el error `'eb' no se reconoce como nombre de un cmdlet`, necesitas instalar el EB CLI:

```powershell
# Instalar EB CLI usando pip
pip install awsebcli

# Verificar que se instaló correctamente
eb --version
```

**Si después de instalar aún no funciona:**
1. Reinicia PowerShell completamente
2. Verifica que Python esté en tu PATH:
   ```powershell
   python --version
   pip --version
   ```
3. Si pip no está en el PATH, usa la ruta completa:
   ```powershell
   python -m pip install awsebcli
   ```
4. Alternativa: Usa `python -m awsebcli` en lugar de `eb`:
   ```powershell
   python -m awsebcli init
   ```

### 3.2 Configurar Credenciales de AWS (Si no lo has hecho)

Antes de ejecutar `eb init`, asegúrate de tener las credenciales de AWS configuradas:

**Opción A: Configurar AWS CLI (Recomendado)**
```powershell
aws configure
```

Ingresa:
- **AWS Access Key ID**: Tu access key
- **AWS Secret Access Key**: Tu secret key  
- **Default region name**: `eu-south-2`
- **Default output format**: `json`

**Verificar que funciona:**
```powershell
aws sts get-caller-identity
```

**Opción B: Ingresar credenciales directamente en `eb init`**

Si prefieres no configurar AWS CLI, puedes ingresar las credenciales cuando `eb init` las pida:
- `aws-access-id`: Tu AWS Access Key ID
- `aws-secret-key`: Tu AWS Secret Access Key

### 3.3 Inicializar Elastic Beanstalk (Primera vez)

```powershell
cd c:\Users\Usuario\Desarrollo\kdi_back
eb init --region eu-south-2
```

O si `eb` no funciona:
```powershell
python -m awsebcli init --region eu-south-2
```

**⚠️ IMPORTANTE - Selección de Región:**

Si tu RDS y Knowledge Base están en **España (eu-south-2)** pero no aparece en la lista de opciones:

**Opción A: Especificar la región directamente**
```powershell
eb init --region eu-south-2
```

**Opción B: Si eu-south-2 no está disponible en EB CLI**
1. Elige la región más cercana disponible (ej: `eu-west-1` - Irlanda)
2. O usa `eu-west-3` (París) que suele estar disponible
3. **Nota**: Puedes tener Elastic Beanstalk en una región y RDS/Knowledge Base en otra, pero es mejor tener todo en la misma región para:
   - Menor latencia
   - Menor costo de transferencia de datos
   - Mayor simplicidad

**Sigue las instrucciones:**
- **Select a region**: 
  - Si `eu-south-2` está disponible, elígela
  - Si no, elige `eu-west-1` (Irlanda) o `eu-west-3` (París) como alternativa cercana
- **Select an application**: Crea nueva aplicación `kdi-back`
- **Select a platform**: Python
- **Select a platform version**: Python 3.11 (o la versión que uses)
- **SSH**: Opcional, pero útil para debugging

**Verificar regiones disponibles para Elastic Beanstalk:**
```powershell
# Listar regiones disponibles
aws elasticbeanstalk describe-regions --region us-east-1
```

**Nota sobre regiones:**
- Elastic Beanstalk puede estar en una región diferente a RDS/Knowledge Base
- La comunicación entre regiones funciona, pero hay latencia adicional
- Si es posible, usa la misma región para todo (eu-south-2 si está disponible)

### 3.4 Diferencia entre `eb init` y `eb create`

**⚠️ IMPORTANTE - Entender la diferencia:**

- **`eb init`**: 
  - ✅ Crea la **aplicación** en AWS (el contenedor lógico, ej: `kdi_back`)
  - ✅ Configura el proyecto **localmente** (crea `.elasticbeanstalk/config.yml`)
  - ❌ **NO crea el entorno** donde corre tu código
  - En AWS verás la aplicación, pero sin entornos dentro

- **`eb create`**: 
  - ✅ Crea el **entorno** dentro de la aplicación (ej: `kdi-back-prod`)
  - ✅ Despliega tu código en instancias EC2
  - ✅ Crea el load balancer, security groups, etc.
  - Este es el comando que realmente despliega tu aplicación

**Estructura en AWS:**
```
Aplicación: kdi_back (creada por `eb init`)
  └── Entorno: kdi-back-prod (creado por `eb create`) ← ESTO ES LO QUE FALTA
      ├── Instancias EC2
      ├── Load Balancer
      └── Tu código ejecutándose
```

**Después de `eb init`, DEBES ejecutar `eb create` para crear el entorno donde correrá tu aplicación.**

### 3.5 Crear Entorno de Producción

**⚠️ RECOMENDACIÓN: Usa EB CLI (no la consola web)**

La mejor opción es usar EB CLI desde la línea de comandos, no la consola web de AWS. EB CLI:
- ✅ Automatiza todo el proceso
- ✅ Facilita actualizaciones futuras (`eb deploy`)
- ✅ Gestiona versiones automáticamente
- ✅ Es más rápido y eficiente

**Opción A: Usar EB CLI (Recomendado)**

Después de ejecutar `eb init`, ahora crea el entorno real en AWS:

```powershell
eb create kdi-back-prod
```

O si `eb` no funciona:
```powershell
python -m awsebcli create kdi-back-prod
```

**⚠️ IMPORTANTE - Versión de Python para Producción:**

**Diferencia entre local y producción:**
- **Local**: Puedes usar Python 3.14 (última versión) para desarrollo
- **Producción (AWS)**: Usa Python 3.11 o 3.12 (más estables y probadas)

**¿Por qué usar una versión diferente?**
- ✅ Python 3.11/3.12 son más estables y probadas en producción
- ✅ Tienen mejor soporte en Elastic Beanstalk
- ✅ Menos problemas de compatibilidad con librerías
- ✅ Tu código Python 3.14 debería funcionar sin problemas en 3.11/3.12 (compatibilidad hacia atrás)

**Versiones recomendadas para producción:**
1. **Python 3.11** (Recomendado) - Muy estable, buen rendimiento
2. **Python 3.12** - También estable, más reciente que 3.11
3. **Python 3.9** - Si necesitas máxima compatibilidad

**Cómo especificar la versión:**

**Opción A: Al crear el entorno (Recomendado)**
```powershell
eb create kdi-back-prod --platform "Python 3.11"
```

**Opción B: Cambiar después de crear**
Si ya creaste con Python 3.14, puedes cambiar la plataforma:
1. Ve a la consola de AWS → Elastic Beanstalk → Tu entorno
2. Configuration → Platform → Modify
3. Cambia a Python 3.11
4. Apply

**Opción C: Editar configuración antes de crear**
Edita `.elasticbeanstalk/config.yml` y cambia:
```yaml
platform:
  name: python-3.11
  version: latest
```

Luego ejecuta:
```powershell
eb create kdi-back-prod
```

O con más opciones:
```powershell
eb create kdi-back-prod `
  --instance-type t3.small `
  --platform "Python 3.11" `
  --envvars FLASK_ENV=production `
  --instance-profile kdi-back-eb-role
```

**Este comando:**
- ✅ Crea el entorno en AWS (esto es lo que falta)
- ✅ Sube tu código
- ✅ Configura las instancias EC2
- ✅ Configura el load balancer
- ⏱️ Tarda varios minutos (5-10 minutos aproximadamente)

**Verificar el progreso:**
```powershell
# Ver el estado del despliegue
eb status

# Ver logs en tiempo real
eb logs --stream
```

**Opción B: Crear desde la Consola Web (Si prefieres)**

Si prefieres usar la consola web de AWS:

1. **Preparar el código para subir:**
   ```powershell
   # Crear un archivo ZIP con tu código
   # Excluye archivos innecesarios (.venv, __pycache__, etc.)
   
   # Opción 1: Usar PowerShell para crear ZIP
   Compress-Archive -Path src,application.py,requirements.txt,.ebextensions -DestinationPath kdi-back.zip -Force
   
   # Opción 2: Usar 7-Zip o WinRAR manualmente
   # Incluye: src/, application.py, requirements.txt, .ebextensions/
   # Excluye: .venv/, __pycache__/, .git/, tests/, data/
   ```

2. **En la consola de AWS:**
   - Ve a **Elastic Beanstalk** → **Create environment**
   - **Platform**: Python
   - **Platform version**: Python 3.11
   - **Application code**: 
     - ✅ **Upload your code** → **Local file** → Selecciona tu `kdi-back.zip`
     - ❌ **Sample application** (NO uses esta opción)
   - **Environment name**: `kdi-back-prod`
   - **Domain**: Deja el predeterminado o personalízalo
   - Click en **Create environment**

3. **Después de crear, configura:**
   - Variables de entorno (ver sección 3.5)
   - IAM Role (ver sección 2.1)
   - Security Groups (ver sección 3.6)

**⚠️ Desventajas de usar la consola web:**
- ❌ Para actualizar, tendrás que crear un nuevo ZIP y subirlo manualmente cada vez
- ❌ Más lento y propenso a errores
- ❌ No gestiona versiones automáticamente

**✅ Ventajas de usar EB CLI:**
- ✅ `eb deploy` actualiza automáticamente
- ✅ Gestiona versiones
- ✅ Más rápido y eficiente
- ✅ Mejor para desarrollo continuo

### 3.3 Configurar Variables de Entorno

Después de crear el entorno, configura las variables de entorno:

**Opción A: Desde la consola de AWS**
1. Ve a **Elastic Beanstalk** → Tu entorno → **Configuration** → **Software**
2. Agrega las siguientes variables de entorno:

```
AWS_REGION=us-east-1
AWS_KNOWLEDGE_BASE_ID=tu_knowledge_base_id
AWS_KNOWLEDGE_BASE_REGION=eu-south-2

DB_HOST=tu-rds-endpoint.xxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=kdi_production
DB_USER=kdi_admin
DB_PASSWORD=tu_contraseña_segura

JWT_SECRET_KEY=genera-una-clave-secreta-muy-larga-y-aleatoria
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

GOOGLE_CLIENT_ID=tu_google_client_id (si aplica)
GOOGLE_CLIENT_SECRET=tu_google_client_secret (si aplica)
INSTAGRAM_CLIENT_ID=tu_instagram_client_id (si aplica)
INSTAGRAM_CLIENT_SECRET=tu_instagram_client_secret (si aplica)
```

**Opción B: Desde CLI (PowerShell)**

En PowerShell, usa comillas y punto y coma para separar variables:
```powershell
eb setenv `
  AWS_REGION=us-east-1 `
  AWS_KNOWLEDGE_BASE_ID=tu_knowledge_base_id `
  AWS_KNOWLEDGE_BASE_REGION=eu-south-2 `
  DB_HOST=tu-rds-endpoint.xxxxx.us-east-1.rds.amazonaws.com `
  DB_PORT=5432 `
  DB_NAME=kdi_production `
  DB_USER=kdi_admin `
  DB_PASSWORD=tu_contraseña_segura `
  JWT_SECRET_KEY=genera-una-clave-secreta-muy-larga-y-aleatoria `
  JWT_ALGORITHM=HS256 `
  JWT_EXPIRATION_HOURS=24
```

O si `eb` no funciona:
```powershell
python -m awsebcli setenv AWS_REGION=us-east-1 AWS_KNOWLEDGE_BASE_ID=tu_knowledge_base_id ...
```

**⚠️ IMPORTANTE**: 
- **NO** incluyas `AWS_ACCESS_KEY_ID` ni `AWS_SECRET_ACCESS_KEY` si usas IAM Roles
- Si necesitas usar credenciales explícitas, usa **AWS Systems Manager Parameter Store** o **AWS Secrets Manager** para mayor seguridad

### 3.7 Configurar Security Group de EB para acceder a RDS

1. Ve a **EC2** → **Security Groups**
2. Encuentra el security group de tu entorno Elastic Beanstalk (nombre como `awseb-e-xxxxx-stack-AWSEBSecurityGroup-xxxxx`)
3. Ve al security group de RDS
4. Agrega regla de entrada:
   - **Type**: PostgreSQL
   - **Port**: 5432
   - **Source**: El security group de Elastic Beanstalk

### 3.8 Desplegar el Código (Si ya creaste el entorno)

```powershell
# Desplegar
eb deploy

# O si es la primera vez
eb deploy kdi-back-prod
```

O si `eb` no funciona:
```powershell
python -m awsebcli deploy
python -m awsebcli deploy kdi-back-prod
```

### 3.9 Verificar el Despliegue

```powershell
# Ver logs
eb logs

# Ver estado
eb status

# Abrir en navegador
eb open
```

O si `eb` no funciona:
```powershell
python -m awsebcli logs
python -m awsebcli status
python -m awsebcli open
```

```bash
# Desplegar
eb deploy

# O si es la primera vez
eb deploy kdi-back-prod
```

### 3.6 Verificar el Despliegue

```bash
# Ver logs
eb logs

# Ver estado
eb status

# Abrir en navegador
eb open
```

## Paso 4: Ejecutar Migraciones de Base de Datos

Después del despliegue, necesitas ejecutar las migraciones. El proyecto tiene **4 archivos de migraciones** que deben ejecutarse en orden:

1. **migrations_player.py** - Tablas de jugadores (user, player_profile, golf_club, player_club_statistics)
2. **migrations_auth.py** - Tablas de autenticación (modifica user, crea auth_tokens)
3. **migrations.py** - Tablas de golf (golf_course, hole, hole_point, obstacle, optimal_shot, strategic_point)
4. **migrations_match.py** - Tablas de partidos (match, match_player, match_hole_score, match_stroke)

### Opción A: Ejecutar todas las migraciones con un solo script (Recomendado)

```powershell
# Configurar variables de entorno en tu .env local
# O exportarlas temporalmente:
$env:DB_HOST="tu-rds-endpoint.xxxxx.us-east-1.rds.amazonaws.com"
$env:DB_PORT="5432"
$env:DB_NAME="kdi_production"
$env:DB_USER="kdi_admin"
$env:DB_PASSWORD="tu_contraseña_segura"

# Ejecutar todas las migraciones en el orden correcto
python scripts/run_all_migrations.py
```

Este script ejecuta todas las migraciones en el orden correcto automáticamente.

### Opción B: Ejecutar migraciones individualmente

Si prefieres ejecutarlas una por una:

```powershell
# 1. Migraciones de jugadores (debe ser primero)
python -m kdi_back.infrastructure.db.migrations_player create_all

# 2. Migraciones de autenticación
python -m kdi_back.infrastructure.db.migrations_auth create_all

# 3. Migraciones de golf
python -m kdi_back.infrastructure.db.migrations create_all

# 4. Migraciones de partidos
python -m kdi_back.infrastructure.db.migrations_match create_all
```

### Opción C: Desde la instancia EC2 (SSH)

```bash
# Conectarte por SSH
eb ssh

# Dentro de la instancia
cd /var/app/current

# Ejecutar todas las migraciones
python scripts/run_all_migrations.py
```

### Opción D: Desde DBeaver

Puedes ejecutar las migraciones directamente desde DBeaver:

1. Conéctate a tu base de datos en DBeaver
2. Click derecho en tu base de datos → **SQL Editor** → **New SQL Script**
3. Abre los archivos de migraciones y ejecuta el SQL manualmente
4. **Nota**: Esto es más tedioso, mejor usa el script de Python

### Verificar que todas las tablas se crearon

Desde DBeaver:
1. Expande tu base de datos → **Schemas** → **public** → **Tables**
2. Deberías ver todas estas tablas:
   - `user`
   - `player_profile`
   - `golf_club`
   - `player_club_statistics`
   - `auth_tokens`
   - `golf_course`
   - `hole`
   - `hole_point`
   - `obstacle`
   - `optimal_shot`
   - `strategic_point`
   - `match`
   - `match_player`
   - `match_hole_score`
   - `match_stroke`

O desde la línea de comandos:
```powershell
# Verificar tablas creadas
python -c "from kdi_back.infrastructure.db.database import Database; db = Database(); cur = db.get_cursor(); cur.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name\"); print('\n'.join([r['table_name'] for r in cur.fetchall()]))"
```

## Paso 5: Importar Datos de Campos de Golf

Si tienes datos de campos de golf para importar:

```bash
# Desde tu máquina local (conectado a RDS)
python -m kdi_back.infrastructure.db.seeders.import_golf_course_from_config data/campos/tu_campo.json
```

## Paso 6: Configurar HTTPS (Producción)

### 6.1 Obtener Certificado SSL

1. Ve a **ACM (Certificate Manager)**
2. Solicita un certificado público
3. Agrega tu dominio (ej: `api.tudominio.com`)
4. Valida el certificado

### 6.2 Configurar Load Balancer

1. Ve a tu entorno de Elastic Beanstalk
2. **Configuration** → **Load balancer**
3. Agrega listener HTTPS en puerto 443
4. Selecciona tu certificado SSL
5. Aplica los cambios

### 6.3 Configurar Dominio Personalizado

1. Ve a **Elastic Beanstalk** → Tu entorno → **Configuration** → **Network**
2. Agrega tu dominio personalizado
3. Configura el DNS de tu dominio para apuntar al CNAME de Elastic Beanstalk

## Monitoreo y Logs

### Ver Logs

**Opción 1: Descargar logs completos (Recomendado)**
```powershell
# Descargar todos los logs
eb logs

# Esto crea un archivo ZIP con todos los logs en el directorio actual
# Busca el archivo más reciente y extráelo para ver los logs
```

**Opción 2: Ver logs desde la consola de AWS**
1. Ve a **AWS Console** → **Elastic Beanstalk** → Tu entorno
2. Click en **Logs** → **Request Logs** → **Last 100 Lines**
3. O click en **Request Logs** → **Full Logs** para descargar todos los logs

**Opción 3: Habilitar streaming de logs (si lo necesitas)**
```powershell
# Habilitar streaming de logs
eb logs --stream --all

# Si da error, habilítalo desde la consola:
# 1. Ve a Elastic Beanstalk → Tu entorno → Configuration
# 2. Software → Log streaming → Enable
# 3. Apply
```

**Opción 4: Ver logs específicos**
```powershell
# Ver logs del engine
eb logs --all

# Ver logs de una instancia específica
eb logs --instance i-xxxxx
```

### CloudWatch

Los logs también están disponibles en **CloudWatch** → **Log groups** → `/aws/elasticbeanstalk/kdi-back-prod/var/log/eb-engine.log`

### Health Checks

El endpoint `/health` está disponible para health checks:
```bash
curl https://tu-dominio.elasticbeanstalk.com/health
```

## Actualizaciones Futuras

Para actualizar la aplicación:

```bash
# Hacer cambios en el código
git add .
git commit -m "Nueva funcionalidad"

# Desplegar
eb deploy
```

## Troubleshooting

### Error: "100% of requests failing with HTTP 5xx" o "ELB health is failing"

Este error indica que la aplicación no está arrancando correctamente o está fallando al procesar peticiones.

**Paso 1: Ver los logs detallados para identificar el error**

```powershell
# Opción A: Descargar logs completos (RECOMENDADO)
eb logs

# Esto crea un archivo ZIP con todos los logs
# Busca el archivo más reciente (ej: kdi-back-pre-xxxxx.zip)
# Extráelo y busca en:
#   - var/log/web.stdout.log (logs de la aplicación)
#   - var/log/eb-engine.log (logs del engine)
#   - var/log/eb-hooks.log (logs de los hooks)

# Opción B: Ver logs desde la consola de AWS
# 1. Ve a Elastic Beanstalk → Tu entorno → Logs
# 2. Request Logs → Last 100 Lines
# 3. Busca errores en los logs

# Opción C: Ver logs específicos
eb logs --all
```

**Errores comunes y soluciones:**

1. **Error: "No module named 'kdi_back'" o errores de importación**
   - **Causa**: El PYTHONPATH no está configurado correctamente para encontrar el módulo en `src/`
   - **Solución**: 
     - Verifica que `.ebextensions/01_python.config` tenga `PYTHONPATH: "/var/app/current:/var/app/current/src:$PYTHONPATH"`
     - El archivo ya está actualizado con esta configuración
     - Después de corregir, redeploya:
     ```powershell
     eb deploy
     ```
   - **Verificación**: Asegúrate de que la estructura sea:
     ```
     /var/app/current/
       ├── application.py
       ├── requirements.txt
       └── src/
           └── kdi_back/
               └── ...
     ```

2. **Error: "Connection refused" o errores de base de datos**
   - **Causa**: Variables de entorno de RDS no configuradas o Security Group incorrecto
   - **Solución**: 
     - Configura las variables de entorno (ver sección 3.7)
     - Verifica que el Security Group de RDS permita conexiones desde EB

3. **Error: "ModuleNotFoundError" o dependencias faltantes**
   - **Causa**: Alguna dependencia en `requirements.txt` no se instaló correctamente
   - **Solución**: 
     - Verifica los logs para ver qué dependencia falla
     - Revisa que `requirements.txt` tenga todas las dependencias

4. **Error: "Application failed to start"**
   - **Causa**: Error en el código al iniciar la aplicación
   - **Solución**: 
     - Revisa los logs completos con `eb logs`
     - Verifica que `application.py` esté correcto
     - Verifica que no haya errores de sintaxis

**Paso 2: Verificar configuración básica**

1. **Verificar que `application.py` existe y es correcto:**
   ```python
   # Debe estar en la raíz y tener:
   from kdi_back.api.main import create_app
   application = create_app()
   ```

2. **Verificar variables de entorno:**
   ```powershell
   eb printenv
   ```
   
   Debe mostrar las variables configuradas. Si están vacías, configúralas (ver sección 3.7).

3. **Verificar logs en la consola de AWS:**
   - Ve a **Elastic Beanstalk** → Tu entorno → **Logs**
   - Click en **Request Logs** → **Last 100 Lines**
   - Busca errores específicos

**Paso 3: Verificar que la aplicación arranca localmente**

Antes de desplegar, asegúrate de que funciona localmente:
```powershell
# Configurar variables de entorno localmente
$env:DB_HOST="localhost"
$env:DB_NAME="db_kdi_test"
# ... otras variables

# Ejecutar localmente
python application.py
```

Si funciona localmente pero no en AWS, el problema es de configuración (variables de entorno, Security Groups, etc.).

### Error: "Instance deployment failed" o "Command failed on instance"

Este error ocurre cuando el despliegue falla durante la instalación o ejecución en la instancia EC2.

**Paso 1: Ver los logs detallados**

```powershell
# Ver logs completos del despliegue
eb logs

# Ver logs en tiempo real
eb logs --stream

# Ver logs específicos del engine
eb logs --all
```

**Paso 2: Verificar errores comunes**

1. **Error: "Yum does not have postgresql-devel available for installation"**:
   - Este error ocurre porque `postgresql-devel` no está disponible en Amazon Linux 2023
   - **Solución**: Como usas `psycopg2-binary` en `requirements.txt`, NO necesitas `postgresql-devel`
   - El archivo `.ebextensions/02_packages.config` ya está corregido para no instalar `postgresql-devel`
   - **Acción**: Termina el entorno y créalo de nuevo:
   ```powershell
   eb terminate kdi-back-pre
   eb create kdi-back-prod --platform "Python 3.11"
   ```

2. **Problema con Python 3.14 (muy reciente)**:
   - Python 3.14 puede tener problemas de compatibilidad con algunas librerías
   - **Solución**: Cambiar a Python 3.11 o 3.12
   ```powershell
   # Terminar el entorno actual
   eb terminate kdi-back-pre
   
   # Crear nuevo con Python 3.11
   eb create kdi-back-prod --platform "Python 3.11"
   ```

3. **Problema con dependencias en requirements.txt**:
   - Verifica que todas las dependencias sean compatibles
   - Algunas librerías pueden no estar disponibles para Python 3.14
   - **Solución**: Usar Python 3.11 que tiene mejor soporte

4. **Problema con la estructura del proyecto**:
   - Verifica que `application.py` esté en la raíz
   - Verifica que `.ebextensions/` tenga las configuraciones correctas
   - Verifica que `requirements.txt` esté en la raíz

5. **Problema con permisos o configuración**:
   - Verifica que el IAM Role esté asignado correctamente
   - Verifica las variables de entorno (aunque esto se hace después)

**Paso 3: Ver logs específicos en la consola de AWS**

1. Ve a **AWS Console** → **Elastic Beanstalk** → Tu entorno `kdi-back-pre`
2. Click en **Logs** → **Request Logs** → **Last 100 Lines**
3. Busca errores relacionados con:
   - Instalación de dependencias
   - Importación de módulos
   - Configuración de WSGI

**Paso 4: Solución rápida - Recrear con Python 3.11**

Si el problema es Python 3.14, la solución más rápida es recrear con Python 3.11:

```powershell
# Terminar el entorno con errores
eb terminate kdi-back-pre

# Editar config.yml para cambiar la plataforma
# O especificar directamente en el comando:
eb create kdi-back-prod --platform "Python 3.11"
```

### Error: No se puede conectar a la base de datos

1. Verifica que el security group de RDS permita conexiones desde el security group de EB
2. Verifica que las variables de entorno `DB_HOST`, `DB_USER`, `DB_PASSWORD` estén correctas
3. Verifica que la base de datos esté en la misma región o VPC

### Error: PostGIS no encontrado

1. Conéctate a RDS y ejecuta: `CREATE EXTENSION IF NOT EXISTS postgis;`
2. Verifica: `SELECT PostGIS_version();`

### Error: Credenciales AWS no encontradas

1. Verifica que el IAM Role esté asignado al entorno de EB
2. Verifica que el role tenga los permisos necesarios para Bedrock
3. Si usas credenciales explícitas, verifica que estén en las variables de entorno

### Error: Módulo no encontrado

1. Verifica que `requirements.txt` incluya todas las dependencias
2. Revisa los logs: `eb logs`

## Costos Estimados (Mensual)

- **Elastic Beanstalk**: ~$15-30 (t3.small, 1 instancia)
- **RDS PostgreSQL**: ~$15-50 (db.t3.micro/small)
- **Load Balancer**: ~$16-20
- **Bedrock**: Pay-per-use (varía según uso)
- **Total estimado**: ~$50-100/mes (desarrollo) o $200-500/mes (producción con alta disponibilidad)

## Seguridad Recomendada

1. ✅ Usa IAM Roles en lugar de credenciales en variables de entorno
2. ✅ Usa AWS Secrets Manager para contraseñas sensibles
3. ✅ Habilita encriptación en RDS
4. ✅ Configura backups automáticos
5. ✅ Usa HTTPS en producción
6. ✅ Limita acceso a RDS solo desde el security group de EB
7. ✅ Rota las contraseñas regularmente
8. ✅ Habilita CloudTrail para auditoría

## Recursos Adicionales

- [Documentación Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/)
- [Documentación RDS PostgreSQL](https://docs.aws.amazon.com/rds/latest/userguide/CHAP_PostgreSQL.html)
- [PostGIS en RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.html#Appendix.PostgreSQL.CommonDBATasks.PostGIS)

