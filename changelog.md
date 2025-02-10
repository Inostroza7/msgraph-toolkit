# Changelog

## [0.1.0] - 10-02-2025

### Añadido
- **Primera versión de `MsGraphBase`:** Configuración y autenticación base para Microsoft Graph API.
  - Gestión de credenciales y tokens
  - Soporte para configuración mediante variables de entorno
  - Validación de credenciales requeridas

- **Nueva clase `AsyncMsGraph`:** Implementación asíncrona del cliente Microsoft Graph.
  - **`async def get_token`:** Obtiene token de acceso usando client credentials flow
  - Inicialización de módulos asíncronos (users, drives, mails)

- **Nueva clase `MsGraph`:** Implementación síncrona del cliente Microsoft Graph.
  - **`def get_token`:** Obtiene token de acceso usando client credentials flow
  - Inicialización de módulos síncronos (users, drives, mails)

- **Módulo `AsyncMails` y `Mails`:**
  - **`list_messages`:** Lista mensajes con filtrado y paginación
  - **`create_message`:** Crea borradores de mensajes
  - **`send_message`:** Envía mensajes existentes
  - **`add_attachment`:** Agrega archivos adjuntos con soporte para archivos grandes

- **Módulo `AsyncDrives` y `Drives`:**
  - **`list_drives`:** Lista unidades disponibles
  - **`get_drive`:** Obtiene información de una unidad
  - **`get_item`:** Obtiene metadata de elementos
  - **`list_followed`:** Lista elementos seguidos
  - **`list_items`:** Lista elementos en una carpeta
  - **`list_changes`:** Rastrea cambios en elementos
  - **`create_folder`:** Crea nuevas carpetas
  - **`update_item`:** Actualiza propiedades de elementos
  - **`upload_content`:** Sube archivos con soporte para archivos grandes
  - **`download_content`:** Descarga contenido de archivos

- **Módulo `AsyncUsers` y `Users`:**
  - **`list_users`:** Lista usuarios con opciones de filtrado
  - **`get_user`:** Obtiene información de usuarios específicos

