# 📚 MsGraph Toolkit

Una potente librería Python para interactuar con Microsoft Graph API de forma sencilla y eficiente.

## ✨ Características

- 🔄 Soporte para operaciones síncronas y asíncronas
- 🔐 Autenticación mediante Client Credentials Flow
- 📧 Gestión completa de correos electrónicos
- 📁 Manejo de archivos y carpetas en OneDrive/SharePoint
- 👥 Administración de usuarios
- 📝 Logging detallado
- ⚡ Optimizado para rendimiento
- 🛡️ Manejo robusto de errores

## 🚀 Instalación

```bash
pip install msgraph-toolkit
```

## 🔧 Configuración

1. Registra una aplicación en Azure Portal
2. Configura las variables de entorno:

```bash
CLIENT_ID=tu_client_id
CLIENT_SECRET=tu_client_secret
TENANT_ID=tu_tenant_id
```README.md

O pasa las credenciales directamente al constructor:

```python
client = AsyncMsGraph(
    client_id="tu_client_id",
    client_secret="tu_client_secret", 
    tenant_id="tu_tenant_id"
)
```

## 📝 Ejemplos de Uso

### Cliente Asíncrono

```python
from msgraph_toolkit import AsyncMsGraph

async def main():
    # Inicializar cliente
    client = AsyncMsGraph()
    
    # Obtener token
    await client.get_token()
    
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

```

### Cliente Síncrono

```python
from msgraph_toolkit import MsGraph

# Inicializar cliente
client = MsGraph()

# Obtener token
client.get_token()

# Listar archivos
files = client.drives.list_items(
    user_id="user@domain.com",
    select="name,size,lastModifiedDateTime"
)
```

## 📦 Módulos Principales

### 📧 Mails
- Listar mensajes
- Crear borradores
- Enviar correos
- Gestionar adjuntos

### 📁 Drives
- Listar drives/carpetas
- Crear carpetas
- Subir/descargar archivos
- Rastrear cambios

### 👥 Users
- Obtener información de usuarios
- Gestionar perfiles
- Administrar permisos

## ⚙️ Configuración Avanzada

### Logging

```python
from msgraph_toolkit.core.log import Log

# Configurar nivel de logging
Log.set_level("DEBUG")
```

### Manejo de Errores

La librería incluye manejo detallado de errores comunes:
- 🔒 Errores de autenticación
- 📛 Errores de permisos
- 🚫 Límites de tamaño
- ⏱️ Timeouts

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. 🍴 Fork el repositorio
2. 🔧 Crea una rama para tu feature
3. 📝 Commit tus cambios
4. 🚀 Push a la rama
5. ✅ Crea un Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo MIT License.