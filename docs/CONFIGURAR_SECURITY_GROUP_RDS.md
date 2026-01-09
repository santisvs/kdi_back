# Guía Paso a Paso: Configurar Security Group de RDS para Elastic Beanstalk

## Problema Común

Error al intentar agregar regla: *"No puede especificar un ID de grupo al que se hace referencia para una regla de CIDR IPv4 existente"*

Este error ocurre cuando intentas modificar una regla existente que usa CIDR (rangos de IP) en lugar de crear una nueva regla con Security Group.

## Solución: Crear una Nueva Regla

### Paso 1: Encontrar el Security Group de Elastic Beanstalk

1. **Abre la consola de AWS** → **Elastic Beanstalk**
2. Selecciona tu entorno (ej: `kdi-back-prod`)
3. Click en **Configuration** (Configuración)
4. En el panel izquierdo, click en **Instances** (Instancias)
5. En la sección **Security**, encuentra **EC2 security groups**
6. **Copia el ID del Security Group** (ej: `sg-0a1b2c3d4e5f6g7h8`)
   - Puede haber más de uno, copia el principal (el primero que aparece)

**Alternativa si no lo encuentras:**
1. Ve a **EC2** → **Instances**
2. Busca las instancias que pertenecen a tu entorno de Elastic Beanstalk
3. Selecciona una instancia
4. En la pestaña **Security**, verás los Security Groups
5. Copia el ID (empieza con `sg-`)

### Paso 2: Ir al Security Group de RDS

1. Ve a **RDS** → **Databases**
2. Selecciona tu instancia de base de datos
3. En la pestaña **Connectivity & security**, encuentra **VPC security groups**
4. **Haz click en el Security Group ID** (se abrirá en una nueva pestaña/ventana)

### Paso 3: Ver Reglas Existentes

1. En la ventana del Security Group, ve a la pestaña **Inbound rules** (Reglas de entrada)
2. **Revisa las reglas existentes**:
   - ¿Hay alguna regla para PostgreSQL (puerto 5432)?
   - Si SÍ existe:
     - Anota si usa CIDR (IP ranges como `0.0.0.0/0` o una IP específica)
     - **NO la modifiques ni elimines** (a menos que quieras reemplazarla)
   - Si NO existe:
     - Simplemente crea una nueva regla

### Paso 4: Agregar Nueva Regla (PASO CRÍTICO)

**⚠️ IMPORTANTE**: Debes crear una **NUEVA regla**, NO modificar una existente.

1. En la pestaña **Inbound rules**, click en **Edit inbound rules** (Editar reglas de entrada)

2. Scroll hacia abajo para ver todas las reglas existentes

3. **NO modifiques reglas existentes**. Si ya existe una regla para 5432:
   - Déjala como está
   - Scroll hasta el final de la lista
   - Verás un botón **"Add rule"** o **"Agregar regla"**

4. Click en **Add rule** (Agregar regla)

5. **Configura la nueva regla**:
   
   **Opción A: Usando el selector de tipo**
   - **Type**: Click en el dropdown y selecciona **PostgreSQL**
   - El puerto 5432 se llenará automáticamente
   
   **Opción B: Si PostgreSQL no aparece**
   - **Type**: Selecciona **Custom TCP**
   - **Port range**: Escribe `5432`

6. **Para el Source (Origen) - ESTO ES CRÍTICO**:
   
   **Método 1: Escribir directamente el ID del Security Group**
   - En el campo **Source**, **NO selecciones "Anywhere-IPv4"** ni uses rangos de IP
   - **Escribe directamente**: `sg-0a1b2c3d4e5f6g7h8` (el ID que copiaste en el Paso 1)
   - AWS debería reconocerlo y mostrar el nombre del Security Group debajo
   
   **Método 2: Usar el selector (si está disponible)**
   - Click en el campo **Source**
   - Busca en el dropdown la opción para seleccionar Security Group
   - Busca el Security Group de Elastic Beanstalk por nombre o ID
   - Selecciónalo
   
   **Método 3: Si aparece "Security group" como opción**
   - En algunos casos, el campo Source tiene un dropdown
   - Busca la opción que dice algo como "Security group" o "Custom"
   - Selecciónala y luego escribe o busca el ID del Security Group

7. **Description** (Opcional pero recomendado):
   - Escribe: "Permitir conexiones desde Elastic Beanstalk"
   - Esto te ayudará a identificar la regla más adelante

8. **Verifica que la regla se vea así**:
   ```
   Type: PostgreSQL (o Custom TCP)
   Protocol: TCP
   Port range: 5432
   Source: sg-0a1b2c3d4e5f6g7h8 (nombre-del-sg)  ← Debe empezar con "sg-"
   Description: Permitir conexiones desde Elastic Beanstalk
   ```

9. Click en **Save rules** (Guardar reglas)

### Paso 5: Verificar que Funcionó

Después de guardar, deberías ver:

- ✅ Una nueva regla en la lista de Inbound rules
- ✅ El Source muestra el ID del Security Group (ej: `sg-...`)
- ✅ NO muestra un rango de IP (como `0.0.0.0/0`)

**Resultado esperado:**
Puedes tener MÚLTIPLES reglas para el puerto 5432:
- Una regla con CIDR (IP) para acceso desde tu computadora
- Una regla nueva con Security Group para acceso desde Elastic Beanstalk

Esto es completamente normal y correcto.

## Solución Alternativa si el Error Persiste

Si después de seguir estos pasos aún obtienes el error, prueba esta alternativa:

### Opción A: Eliminar y Recrear (SOLO si es seguro)

**⚠️ ADVERTENCIA**: Esto puede interrumpir conexiones existentes. Solo hazlo si:
- No hay otras aplicaciones importantes conectándose a RDS
- O si la regla existente usa `0.0.0.0/0` (cualquier IP)

1. Elimina la regla existente para PostgreSQL (5432)
2. Crea una nueva regla usando el Security Group de EB
3. Si necesitas acceso desde tu IP local también, crea otra regla adicional

### Opción B: Usar la Regla Existente Temporalmente

Si la regla existente usa `0.0.0.0/0` (permite conexiones desde cualquier lugar):
- Técnicamente, Elastic Beanstalk YA puede conectarse
- El problema podría ser otro (variables de entorno, etc.)
- Aunque es menos seguro, funcionará para pruebas

**Para producción, es mejor usar Security Groups específicos.**

## Verificación Final

Después de configurar la regla:

1. **Espera 1-2 minutos** para que los cambios surtan efecto

2. **Verifica los logs de Elastic Beanstalk**:
   ```powershell
   eb logs --stream
   ```
   Busca mensajes como:
   - ✅ "Pool de conexiones a PostgreSQL creado exitosamente"
   - ❌ "Error al crear el pool de conexiones"

3. **Prueba el endpoint**:
   ```powershell
   curl -X POST https://tu-entorno.elasticbeanstalk.com/auth/register `
     -H "Content-Type: application/json" `
     -d '{"email":"test@example.com","username":"testuser","password":"password123"}'
   ```

## Errores Comunes y Soluciones

### Error: "No puede especificar un ID de grupo al que se hace referencia para una regla de CIDR IPv4 existente"

**Causa**: Estás intentando modificar una regla existente en lugar de crear una nueva.

**Solución**: 
- NO modifiques la regla existente
- Crea una NUEVA regla usando "Add rule"
- Puedes tener múltiples reglas para el mismo puerto

### Error: El campo Source no acepta el ID del Security Group

**Causa**: Estás usando el formato incorrecto o el campo no está configurado para Security Groups.

**Solución**:
- Asegúrate de escribir el ID completo empezando con `sg-`
- Verifica que no estés en el modo "CIDR" o "IP ranges"
- Algunas interfaces tienen un selector diferente para Security Groups

### No veo el Security Group de EB en el dropdown

**Causa**: Puede que estén en VPCs diferentes o el Security Group aún no existe.

**Solución**:
- Escribe el ID manualmente: `sg-xxxxxxxxxxxxx`
- Verifica que ambos Security Groups estén en la misma VPC
- Asegúrate de haber copiado el ID correcto del Security Group de EB

## Notas Adicionales

- ✅ Puedes tener múltiples reglas para el mismo puerto
- ✅ Una regla puede usar CIDR (IP) y otra puede usar Security Group
- ✅ El orden de las reglas no importa
- ✅ Los cambios en Security Groups son inmediatos (no requiere reinicio)
- ⚠️ Usar Security Groups es más seguro que usar rangos de IP
- ⚠️ `0.0.0.0/0` permite acceso desde cualquier lugar (solo para desarrollo/testing)





