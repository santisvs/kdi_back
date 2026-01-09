# Solución: Error de Permisos de Bedrock en Elastic Beanstalk

## Problema

Al ejecutar el endpoint `/golf`, obtienes el siguiente error:

```
An error occurred (AccessDeniedException) when calling the ConverseStream operation: 
User: arn:aws:sts::453194202736:assumed-role/aws-elasticbeanstalk-ec2-role/i-000a9b6c8340de067 
is not authorized to perform: bedrock:InvokeModelWithResponseStream on resource: 
arn:aws:bedrock:us-east-1:453194202736:inference-profile/us.amazon.nova-lite-v1:0 
because no identity-based policy allows the bedrock:InvokeModelWithResponseStream action
```

**Causa**: El rol IAM `aws-elasticbeanstalk-ec2-role` asignado a las instancias EC2 de Elastic Beanstalk no tiene permisos para invocar Bedrock.

## Solución

Tienes dos opciones:

### Opción 1: Agregar Permisos al Rol Existente (Más Rápido)

Si ya tienes un rol IAM asignado a tu entorno de Elastic Beanstalk, simplemente agrega los permisos necesarios:

#### Paso 1: Identificar el Rol Actual

1. Ve a la consola de AWS → **Elastic Beanstalk** → Tu entorno (ej: `kdi-back-prod`)
2. Ve a **Configuration** → **Security**
3. Busca **IAM instance profile** - Este es el rol que necesitas modificar (ej: `aws-elasticbeanstalk-ec2-role`)

#### Paso 2: Agregar Permisos de Bedrock al Rol

1. Ve a **IAM** → **Roles**
2. Busca y selecciona el rol que identificaste (ej: `aws-elasticbeanstalk-ec2-role`)
3. Click en **Add permissions** → **Create inline policy** (o **Attach policies** si prefieres usar una política administrada)

#### Paso 3: Crear Política Personalizada (Recomendado)

**Opción A: Política Administrada (Más Fácil)**

1. Click en **Add permissions** → **Attach policies**
2. Busca y selecciona: **`AmazonBedrockFullAccess`**
3. Click en **Add permissions**

**Opción B: Política Personalizada (Más Segura - Recomendado para Producción)**

1. Click en **Add permissions** → **Create inline policy**
2. Selecciona la pestaña **JSON**
3. Pega la siguiente política:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:Converse",
        "bedrock:ConverseStream",
        "bedrock:Retrieve",
        "bedrock:RetrieveAndGenerate"
      ],
      "Resource": [
        "arn:aws:bedrock:*:*:inference-profile/*",
        "arn:aws:bedrock:*:*:foundation-model/*"
      ]
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

4. Click en **Next**
5. **Policy name**: `BedrockInvokePolicy` (o el nombre que prefieras)
6. Click en **Create policy**

#### Paso 4: Verificar que los Permisos se Aplicaron

1. En la página del rol, verifica que la política aparezca en la lista de políticas
2. Los cambios se aplican inmediatamente - no necesitas reiniciar las instancias

#### Paso 5: Probar el Endpoint

```bash
# Probar el endpoint /golf
curl -X POST https://tu-dominio.elasticbeanstalk.com/golf \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.4168,
    "longitude": -3.7038,
    "query": "Estoy a 150 metros del hoyo"
  }'
```

### Opción 2: Crear un Nuevo Rol y Asignarlo (Más Limpio)

Si prefieres crear un rol específico para tu aplicación:

#### Paso 1: Crear Nuevo Rol IAM

1. Ve a **IAM** → **Roles** → **Create role**
2. Selecciona **AWS service** → **Elastic Beanstalk**
3. Selecciona **Elastic Beanstalk - Compute**
4. Click en **Next**

#### Paso 2: Agregar Permisos

**Opción A: Política Administrada**
- Adjunta: **`AmazonBedrockFullAccess`**

**Opción B: Política Personalizada**
- Crea una política inline con el JSON de la Opción 1, Paso 3

#### Paso 3: Nombrar el Rol

- **Role name**: `kdi-back-bedrock-role` (o el nombre que prefieras)
- **Description**: "Rol para instancias EC2 de Elastic Beanstalk con acceso a Bedrock"
- Click en **Create role**

#### Paso 4: Asignar el Rol al Entorno de Elastic Beanstalk

1. Ve a **Elastic Beanstalk** → Tu entorno → **Configuration**
2. Click en **Security** → **Edit**
3. En **IAM instance profile**, selecciona el nuevo rol (ej: `kdi-back-bedrock-role`)
4. Click en **Apply**
5. Espera a que se complete la actualización (puede tardar unos minutos)

## Verificación

Después de aplicar los cambios, verifica que funciona:

### 1. Verificar desde los Logs

```powershell
# Ver logs en tiempo real
eb logs --stream

# O descargar logs
eb logs
```

Busca en los logs que no aparezcan errores de `AccessDeniedException`.

### 2. Probar el Endpoint

```bash
# Probar endpoint /golf
curl -X POST https://tu-dominio.elasticbeanstalk.com/golf \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.4168,
    "longitude": -3.7038,
    "query": "Estoy a 150 metros del hoyo, hay viento en contra"
  }'
```

Deberías recibir una respuesta con la recomendación del agente de golf.

## Permisos Necesarios Explicados

Los permisos que necesitas son:

- **`bedrock:InvokeModel`**: Para invocar modelos de Bedrock (método tradicional)
- **`bedrock:InvokeModelWithResponseStream`**: Para invocar modelos con streaming (método tradicional con streaming)
- **`bedrock:Converse`**: Para usar la API Converse de Bedrock (método nuevo)
- **`bedrock:ConverseStream`**: Para usar la API Converse con streaming (método nuevo con streaming) - **Este es el que está fallando**
- **`bedrock:Retrieve`**: Para consultar Knowledge Bases
- **`bedrock:RetrieveAndGenerate`**: Para usar Retrieve and Generate
- **`bedrock:GetFoundationModel`**: Para obtener información de modelos
- **`bedrock:ListFoundationModels`**: Para listar modelos disponibles

**Nota**: La librería `strands` que usas internamente utiliza `ConverseStream`, por eso necesitas específicamente `bedrock:ConverseStream`.

## Troubleshooting

### Error persiste después de agregar permisos

1. **Verifica que el rol esté asignado correctamente**:
   - Elastic Beanstalk → Tu entorno → Configuration → Security
   - Verifica que el IAM instance profile sea el correcto

2. **Verifica que los permisos se hayan guardado**:
   - IAM → Roles → Tu rol → Permissions
   - Debe aparecer la política que creaste

3. **Espera unos minutos**: Los cambios de IAM pueden tardar unos segundos en propagarse

4. **Reinicia las instancias** (si es necesario):
   ```powershell
   # Reiniciar el entorno
   eb restart
   ```

### Error: "Resource not found" o "Model not found"

Si después de agregar permisos obtienes un error de que el modelo no se encuentra:

1. Verifica que el modelo `us.amazon.nova-lite-v1:0` esté disponible en tu región
2. Verifica que tengas acceso al modelo en la consola de Bedrock
3. Algunos modelos requieren solicitar acceso primero en la consola de Bedrock

### Verificar Acceso al Modelo

1. Ve a **AWS Console** → **Bedrock** → **Foundation models**
2. Busca `Amazon Nova Lite`
3. Verifica que esté disponible en tu región (ej: `us-east-1`)
4. Si no está disponible, solicita acceso o cambia a otra región

## Notas Importantes

1. **No necesitas credenciales explícitas**: Si usas IAM Roles, NO incluyas `AWS_ACCESS_KEY_ID` ni `AWS_SECRET_ACCESS_KEY` en las variables de entorno de Elastic Beanstalk.

2. **Región del modelo**: El modelo `us.amazon.nova-lite-v1:0` tiene el prefijo `us.`, lo que indica que está en la región `us-east-1`. Asegúrate de que:
   - Tu variable de entorno `AWS_REGION` esté configurada correctamente
   - O que el código use la región correcta al crear el cliente de Bedrock

3. **Permisos mínimos**: Para producción, usa la política personalizada (Opción B) en lugar de `AmazonBedrockFullAccess` para seguir el principio de menor privilegio.

## Referencias

- [Documentación de IAM para Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html)
- [Permisos de Bedrock](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_Operations.html)
- [Configurar IAM Roles en Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/iam-instanceprofile.html)




