# 🌐 Microsoft Graph Toolkit

Cliente Python para interactuar con Microsoft Graph API de forma sencilla y eficiente.

## ✨ Características

- 🔄 Soporte para operaciones síncronas y asíncronas
- 📨 Gestión de correos y archivos adjuntos
- 💾 Manejo de OneDrive y SharePoint
- 👥 Administración de usuarios
- 🔐 Autenticación mediante client credentials flow
- 📝 Logging integrado
- ⚡ Cliente HTTP moderno con httpx

## 🚀 Instalación

```bash
pip install msgraph-toolkit
```

## 🛠️ Configuración

1. Registra una aplicación en Azure Portal
2. Configura las variables de entorno:

```bash
CLIENT_ID="tu-client-id"
CLIENT_SECRET="tu-client-secret"
TENANT_ID="tu-tenant-id"
```

O pasa las credenciales directamente al inicializar el cliente:

```python
from msgraph_toolkit import MsGraph

client = MsGraph(
    client_id="tu-client-id",
    client_secret="tu-client-secret",
    tenant_id="tu-tenant-id"
)
```

## 📚 Uso

### Cliente Síncrono

```python
from msgraph_toolkit import MsGraph

# Inicializar cliente
client = MsGraph()

# Listar usuarios
users = client.users.list_users(
    select="displayName,mail",
    filter="startsWith(displayName,'A')"
)

# Obtener drives
drives = client.drives.list_drives(user_id="user@domain.com")
```

### Cliente Asíncrono

```python
from msgraph_toolkit import AsyncMsGraph
import asyncio

async def main():
    # Inicializar cliente
    client = AsyncMsGraph()
    
    # Listar mensajes
    messages = await client.mails.list_messages(
        select="subject,receivedDateTime",
        top=10
    )
    
    # Crear carpeta en OneDrive
    folder = await client.drives.create_folder(
        name="Nueva Carpeta",
        user_id="user@domain.com"
    )

asyncio.run(main())
```

## 📦 Módulos

### 📧 Mails

Gestión de correos electrónicos:

```python
# Listar mensajes
messages = client.mails.list_messages(
    select="subject,from,receivedDateTime",
    filter="receivedDateTime ge 2024-01-01",
    top=50
)

# Crear y enviar mensaje
message = client.mails.create_message(
    subject="Asunto",
    body="Contenido del mensaje",
    to_recipients=["user@domain.com"],
    body_type="HTML"
)
client.mails.send_message(message['id'])

# Adjuntar archivo
client.mails.add_attachment(
    message_id=message['id'],
    file_path="documento.pdf"
)
```

### 💾 Drives

Operaciones con OneDrive y SharePoint:

```python
# Listar archivos
items = client.drives.list_items(
    user_id="user@domain.com",
    select="name,size,lastModifiedDateTime"
)

# Crear carpeta
folder = client.drives.create_folder(
    name="Nueva Carpeta",
    user_id="user@domain.com"
)

# Descargar archivo
content = client.drives.download_content(
    item_id="item-id",
    user_id="user@domain.com"
)
```

### 👥 Users

Gestión de usuarios:

```python
# Listar usuarios
users = client.users.list_users(
    select="displayName,mail,jobTitle",
    filter="accountEnabled eq true"
)

# Obtener usuario específico
user = client.users.get_user(
    user_id="user@domain.com",
    select="displayName,mail,department"
)
```

## 🔑 Permisos

Los permisos requeridos dependen de las operaciones:

- `Mail.Read`: Leer correos
- `Mail.ReadWrite`: Crear/modificar correos
- `Mail.Send`: Enviar correos
- `Files.Read`: Leer archivos
- `Files.ReadWrite`: Crear/modificar archivos
- `User.Read.All`: Leer usuarios

## ⚠️ Manejo de Errores

La librería incluye manejo de errores específicos:

```python
try:
    messages = client.mails.list_messages()
except PermissionError:
    print("No tiene los permisos necesarios")
except ValueError:
    print("Parámetros inválidos")
except Exception as e:
    print(f"Error: {str(e)}")
```

## 📝 Logging

La librería utiliza logging integrado:

```python
from msgraph_toolkit.core.log import Log

logger = Log(__name__)
logger.setLevel("DEBUG")
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.