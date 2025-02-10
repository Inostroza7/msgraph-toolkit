# Changelog

## [0.1.3] - 10-02-2025

### Mejorado

- **Módulo `Mails`:** Funcionalidad extendida
  - **`add_attachment`:** Ahora soporta adjuntar archivos por ruta o bytes
  - Detección automática de tipo MIME
  - Manejo unificado de archivos grandes


## [0.1.2] - 12-02-2025

### Añadido

- **Módulo `Drives`:** Implementación síncrona completada

  - **`create_folder`:** Crea carpetas con manejo de conflictos y permisos
  - Soporte para crear en raíz o subcarpetas
  - Validación de parámetros y manejo de errores mejorado

- **Módulo `Mails`:** Nuevas funcionalidades
  - **`add_attachment_bytes`:** Permite adjuntar archivos usando bytes directamente
  - Soporte para archivos grandes usando sesiones de carga
  - Detección automática de tipo MIME


## [0.1.1] - 11-02-2025

### Cambiado

- **Módulo `Users`:** Renombrado de métodos para mayor claridad
  - `list()` renombrado a `list_users()`
  - `get()` renombrado a `get_user()`

### Añadido

- **Módulo `Drives`:** Implementación síncrona completa
  - **`update_item`:** Actualiza propiedades de elementos
  - **`upload_content`:** Sube archivos hasta 250MB
  - **`download_content`:** Descarga contenido de archivos con soporte para rangos

### Mejorado

- **Manejo de errores:** Mensajes más descriptivos y específicos para cada código de error
- **Documentación:** Mejorada la documentación de los métodos con ejemplos y notas de uso

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
