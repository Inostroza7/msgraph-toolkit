from typing import Optional
import httpx
from ..core.log import Log
import json
import os
import mimetypes
import base64

logger = Log(__name__)

class AsyncMails:
    def __init__(self, client):
        self.client = client
    
    async def list_messages(
        self,
        user_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        select: Optional[str] = None,
        filter: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        body_type: Optional[str] = None
    ) -> dict:
        """
        Lista los mensajes del buzón de un usuario.
        
        Args:
            user_id (str, optional): ID o userPrincipalName del usuario
            folder_id (str, optional): ID de la carpeta específica
            select (str, optional): Propiedades específicas a retornar
            filter (str, optional): Filtro OData
            orderby (str, optional): Ordenamiento OData
            top (int, optional): Número máximo de mensajes (1-1000)
            body_type (str, optional): Formato del cuerpo ('text' o 'html')
            
        Returns:
            dict: Lista de mensajes y nextLink para paginación
            
        Raises:
            ValueError: Si los parámetros no son válidos
            HTTPStatusError: Si hay error en la petición
            PermissionError: Si no se tienen los permisos necesarios
            
        Note:
            - Por defecto retorna 10 mensajes por página
            - Para mejorar el rendimiento, use select y top apropiadamente
            - El cuerpo de los mensajes se retorna en HTML por defecto
            - Con client credentials se requiere especificar user_id
        """
        try:
            if not self.client.token:
                await self.client.get_token()
                
            # Validar que se proporcione user_id con client credentials
            if not user_id and not self.client.is_delegated:
                raise ValueError(
                    "Debe proporcionar user_id cuando usa client credentials. "
                    "Para acceder a /me use autenticación delegada"
                )
                
            # Validar top
            if top is not None and not (1 <= top <= 1000):
                raise ValueError("top debe estar entre 1 y 1000")
                
            # Validar body_type
            if body_type and body_type not in ['text', 'html']:
                raise ValueError("body_type debe ser 'text' o 'html'")
                
            # Construir URL base
            if user_id:
                base_url = f"{self.client.base_url}/users/{user_id}"
            else:
                base_url = f"{self.client.base_url}/me"
                
            # Construir URL final
            if folder_id:
                url = f"{base_url}/mailFolders/{folder_id}/messages"
            else:
                url = f"{base_url}/messages"
                
            # Parámetros de consulta
            params = {}
            if select:
                params['$select'] = select
            if filter:
                params['$filter'] = filter
            if orderby:
                params['$orderby'] = orderby
            if top:
                params['$top'] = str(top)
                
            # Headers
            headers = {
                'Authorization': f'Bearer {self.client.token}'
            }
            if body_type:
                headers['Prefer'] = f'outlook.body-content-type="{body_type}"'
                
            # Realizar petición GET
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                logger.info(
                    f"Mensajes listados exitosamente "
                    f"({len(response.json()['value'])} mensajes)"
                )
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "InefficientFilter" in e.response.text:
                    raise ValueError(
                        "La combinación de filter y orderby es inválida. "
                        "Asegúrese que las propiedades en orderby:"
                        "\n- También aparezcan en filter"
                        "\n- Estén en el mismo orden que en filter"
                        "\n- Aparezcan antes que otras propiedades en filter"
                    ) from e
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Mail.ReadBasic o Mail.Read"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Mail.ReadBasic o Mail.Read"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para listar mensajes. "
                    "Se requiere Mail.ReadBasic o Mail.Read"
                ) from e
            elif e.response.status_code == 504:
                logger.error("Error 504: Tiempo de espera agotado")
                raise TimeoutError(
                    "La operación tardó demasiado. "
                    "Intente reducir el número de propiedades (select) o mensajes (top)"
                ) from e
            raise  # Re-lanza otros errores HTTP
    
    async def create_message(
        self,
        subject: str,
        body: str,
        to_recipients: list,
        user_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        body_type: str = "HTML",
        importance: str = "normal",
        cc_recipients: Optional[list] = None,
        bcc_recipients: Optional[list] = None,
        reply_to: Optional[list] = None,
        message_headers: Optional[list[dict]] = None,
        mime_content: Optional[str] = None
    ) -> dict:
        """
        Crea un borrador de mensaje nuevo.
        
        Args:
            subject (str): Asunto del mensaje
            body (str): Contenido del mensaje
            to_recipients (list): Lista de destinatarios en formatos flexibles:
                - ["user@domain.com"]
                - [("user@domain.com", "User Name")]
                - [{"address": "user@domain.com", "name": "User Name"}]
            user_id (str, optional): ID o userPrincipalName del usuario
            folder_id (str, optional): ID de la carpeta donde crear el borrador
            body_type (str): Tipo de contenido del cuerpo ('HTML' o 'text')
            importance (str): Importancia del mensaje ('low', 'normal', 'high')
            cc_recipients (list, optional): Lista de destinatarios en copia
            bcc_recipients (list, optional): Lista de destinatarios en copia oculta
            reply_to (list, optional): Lista de direcciones de respuesta
            message_headers (list[dict], optional): Headers personalizados del mensaje
            mime_content (str, optional): Contenido MIME codificado en base64
            
        Returns:
            dict: Mensaje creado
            
        Raises:
            ValueError: Si los parámetros no son válidos
            HTTPStatusError: Si hay error en la petición
            PermissionError: Si no se tienen los permisos necesarios
        """
        try:
            if not self.client.token:
                await self.client.get_token()
                
            # Validar que se proporcione user_id con client credentials
            if not user_id and not self.client.is_delegated:
                raise ValueError(
                    "Debe proporcionar user_id cuando usa client credentials. "
                    "Para acceder a /me use autenticación delegada"
                )
                
            # Validar parámetros
            if mime_content:
                if any([body, subject, to_recipients, message_headers]):
                    raise ValueError(
                        "Cuando se proporciona mime_content no se pueden usar "
                        "otros parámetros del mensaje"
                    )
            else:
                if not all([subject, body, to_recipients]):
                    raise ValueError(
                        "Debe proporcionar subject, body y to_recipients"
                    )
                if body_type.upper() not in ['HTML', 'TEXT']:
                    raise ValueError("body_type debe ser 'HTML' o 'text'")
                if importance.lower() not in ['low', 'normal', 'high']:
                    raise ValueError("importance debe ser 'low', 'normal' o 'high'")
                
            # Construir URL base
            if user_id:
                base_url = f"{self.client.base_url}/users/{user_id}"
            else:
                base_url = f"{self.client.base_url}/me"
                
            # Construir URL final
            if folder_id:
                url = f"{base_url}/mailFolders/{folder_id}/messages"
            else:
                url = f"{base_url}/messages"
                
            # Headers de la petición HTTP
            request_headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Type': 'text/plain' if mime_content else 'application/json'
            }
            
            # Datos del mensaje
            if mime_content:
                data = mime_content
            else:
                data = {
                    "subject": subject,
                    "importance": importance.lower(),
                    "body": {
                        "contentType": body_type.lower(),
                        "content": body
                    },
                    "toRecipients": self._process_recipients(to_recipients)
                }
                
                if cc_recipients:
                    data["ccRecipients"] = self._process_recipients(cc_recipients)
                if bcc_recipients:
                    data["bccRecipients"] = self._process_recipients(bcc_recipients)
                if reply_to:
                    data["replyTo"] = self._process_recipients(reply_to)
            
            # Agregar headers del mensaje si se proporcionan
            if message_headers and len(message_headers) > 0:
                # Validar formato de los headers
                for header in message_headers:
                    if not isinstance(header, dict) or 'name' not in header or 'value' not in header:
                        raise ValueError(
                            "Formato inválido de message_headers. Debe ser: "
                            '[{"name": "x-custom-header", "value": "custom value"}]'
                        )
                data["internetMessageHeaders"] = message_headers
            
            # Realizar petición POST
            async with httpx.AsyncClient() as client:
                # Log detallado de la petición
                logger.debug("Request details:")
                logger.debug(f"URL: {url}")
                logger.debug(f"Headers: {request_headers}")
                logger.debug(f"Data: {json.dumps(data, indent=2)}")
                
                response = await client.post(
                    url, 
                    content=data if mime_content else None,
                    json=data if not mime_content else None,
                    headers=request_headers
                )
                
                # Log detallado de la respuesta
                logger.debug("Response details:")
                logger.debug(f"Status: {response.status_code}")
                logger.debug(f"Headers: {dict(response.headers)}")
                try:
                    body = response.json()
                    logger.debug(f"Body: {json.dumps(body, indent=2)}")
                except:
                    logger.debug(f"Body: {response.text}")
                
                if response.status_code >= 400:
                    logger.error(f"Error {response.status_code}: {response.text}")
                
                response.raise_for_status()
                
                logger.info(f"Borrador creado exitosamente")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "Invalid base64 string" in e.response.text:
                    raise ValueError(
                        "El contenido MIME proporcionado no es una cadena base64 válida"
                    ) from e
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Mail.ReadWrite"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Mail.ReadWrite"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para crear mensajes. Se requiere Mail.ReadWrite"
                ) from e
            elif e.response.status_code == 413:
                logger.error("Error 413: Contenido demasiado grande")
                raise ValueError(
                    "El contenido MIME excede el límite de 4MB"
                ) from e
            raise  # Re-lanza otros errores HTTP
    
    async def send_message(
        self,
        message_id: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        Envía un mensaje en borrador existente.
        
        Args:
            message_id (str): ID del mensaje en borrador
            user_id (str, optional): ID o userPrincipalName del usuario
            
        Raises:
            ValueError: Si no se proporciona message_id
            PermissionError: Si no se tienen los permisos necesarios
            
        Example:
            >>> mails.send_message(
            ...     message_id="123",
            ...     user_id="user@domain.com"
            ... )
        """
        try:
            if not self.client.token:
                await self.client.get_token()
                
            # Validaciones
            if not user_id and not self.client.is_delegated:
                raise ValueError(
                    "Debe proporcionar user_id cuando usa client credentials. "
                    "Para acceder a /me use autenticación delegada"
                )
                
            if not message_id:
                raise ValueError("Debe proporcionar message_id")
                
            # Construir URL
            if user_id:
                base_url = f"{self.client.base_url}/users/{user_id}"
            else:
                base_url = f"{self.client.base_url}/me"
                
            url = f"{base_url}/messages/{message_id}/send"
                
            # Headers
            headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Length': '0'
            }
            
            # Realizar petición POST
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers)
                
                if response.status_code == 202:
                    logger.info("Mensaje enviado exitosamente")
                    return
                    
                response.raise_for_status()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Mail.Send"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Mail.Send"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para enviar mensajes. Se requiere Mail.Send"
                ) from e
            elif e.response.status_code == 404:
                logger.error("Error 404: Mensaje no encontrado")
                raise ValueError(
                    "El mensaje especificado no existe o no es un borrador"
                ) from e
            raise
    
    async def add_attachment(
        self,
        message_id: str,
        file_path: Optional[str] = None,
        content: Optional[bytes] = None,
        file_name: Optional[str] = None,
        user_id: Optional[str] = None,
        is_inline: bool = False,
        content_type: Optional[str] = None,
    ) -> dict:
        """
        Agrega un archivo adjunto a un mensaje de forma simplificada.
        
        Args:
            message_id (str): ID del mensaje
            file_path (str, optional): Ruta al archivo que se quiere adjuntar
            content (bytes, optional): Contenido del archivo en bytes
            file_name (str, optional): Nombre del archivo cuando se usa content
            user_id (str, optional): ID o userPrincipalName del usuario
            is_inline (bool): Si el adjunto debe mostrarse en línea en el mensaje
            content_type (str, optional): Tipo MIME del contenido
            
        Returns:
            dict: Información del adjunto creado
            
        Raises:
            ValueError: Si no se proporciona file_path o content+file_name
            FileNotFoundError: Si no se encuentra el archivo
            
        Example:
            # Usando ruta de archivo
            >>> await mails.add_attachment(
            ...     message_id="123",
            ...     file_path="documento.pdf"
            ... )
            
            # Usando bytes
            >>> with open('documento.pdf', 'rb') as f:
            ...     content = f.read()
            >>> await mails.add_attachment(
            ...     message_id="123",
            ...     content=content,
            ...     file_name="documento.pdf"
            ... )
        """
        # Validar que se proporcione al menos una forma de contenido
        if file_path is None and (content is None or file_name is None):
            raise ValueError(
                "Debe proporcionar file_path o la combinación de content y file_name"
            )
        if file_path is not None and (content is not None or file_name is not None):
            raise ValueError(
                "No puede proporcionar file_path junto con content o file_name"
            )

        try:
            # Caso 1: Usando file_path
            if file_path:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
                
                # Obtener tamaño y tipo del archivo
                file_size = os.path.getsize(file_path)
                if not content_type:
                    content_type, _ = mimetypes.guess_type(file_path)
                    if not content_type:
                        content_type = 'application/octet-stream'
                
                # Obtener nombre del archivo
                file_name = os.path.basename(file_path)
                
                # Leer contenido
                with open(file_path, 'rb') as f:
                    content = f.read()

            # Caso 2: Usando content+file_name
            else:
                file_size = len(content)
                if not content_type:
                    content_type, _ = mimetypes.guess_type(file_name)
                    if not content_type:
                        content_type = 'application/octet-stream'

            # Para archivos pequeños (<3MB) usar carga directa
            if file_size <= 3 * 1024 * 1024:
                encoded_content = base64.b64encode(content).decode()
                return await self._add_attachment_raw(
                    message_id=message_id,
                    name=file_name,
                    content_bytes=encoded_content,
                    user_id=user_id,
                    is_inline=is_inline,
                    content_type=content_type
                )
            
            # Para archivos grandes usar sesión de carga
            if file_size > 150 * 1024 * 1024:  # 150MB
                raise ValueError("El archivo excede el límite máximo de 150MB")
            
            session = await self._create_upload_session(
                message_id=message_id,
                name=file_name,
                size=file_size,
                user_id=user_id,
                is_inline=is_inline
            )
            
            # Subir por chunks
            chunk_size = 4 * 1024 * 1024  # 4MB por chunk
            for start in range(0, file_size, chunk_size):
                chunk = content[start:start + chunk_size]
                end = start + len(chunk) - 1
                
                await self._upload_chunk(
                    upload_url=session['uploadUrl'],
                    chunk=chunk,
                    start=start,
                    end=end,
                    total=file_size
                )
            
            logger.info(f"Adjunto '{file_name}' agregado exitosamente")
            return session
            
        except Exception as e:
            logger.error(f"Error al agregar adjunto: {str(e)}")
            raise

    async def _create_upload_session(
        self,
        message_id: str,
        name: str,
        size: int,
        user_id: Optional[str] = None,
        is_inline: bool = False
    ) -> dict:
        """Crea una sesión de carga para subir un archivo grande"""
        if not self.client.token:
            await self.client.get_token()
        
        # Construir URL
        base_url = f"{self.client.base_url}/users/{user_id}" if user_id else f"{self.client.base_url}/me"
        url = f"{base_url}/messages/{message_id}/attachments/createUploadSession"
        
        # Datos de la sesión
        data = {
            "AttachmentItem": {
                "attachmentType": "file",
                "name": name,
                "size": size,
                "isInline": is_inline
            }
        }
        
        # Crear sesión
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=data,
                headers={'Authorization': f'Bearer {self.client.token}'}
            )
            response.raise_for_status()
            return response.json()

    async def _upload_chunk(
        self,
        upload_url: str,
        chunk: bytes,
        start: int,
        end: int,
        total: int
    ) -> None:
        """Sube un rango de bytes usando la sesión de carga"""
        headers = {
            'Content-Length': str(len(chunk)),
            'Content-Range': f'bytes {start}-{end}/{total}'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(upload_url, content=chunk, headers=headers)
            response.raise_for_status()

    async def _add_attachment_raw(
        self,
        message_id: str,
        name: str,
        content_bytes: str,
        user_id: Optional[str] = None,
        is_inline: bool = False,
        content_type: Optional[str] = None,
    ) -> dict:
        """Método interno que maneja la lógica original de add_attachment"""
        try:
            if not self.client.token:
                await self.client.get_token()
                
            # Validar que se proporcione user_id con client credentials
            if not user_id and not self.client.is_delegated:
                raise ValueError(
                    "Debe proporcionar user_id cuando usa client credentials. "
                    "Para acceder a /me use autenticación delegada"
                )
                
            # Validar parámetros
            if not message_id:
                raise ValueError("Debe proporcionar message_id")
                
            # Validar tamaño del adjunto
            if content_bytes and len(content_bytes) > 3 * 1024 * 1024:  # 3MB
                raise ValueError("El adjunto excede el límite de 3MB")
                
            # Construir URL base
            if user_id:
                base_url = f"{self.client.base_url}/users/{user_id}"
            else:
                base_url = f"{self.client.base_url}/me"
                
            # Construir URL final
            url = f"{base_url}/messages/{message_id}/attachments"
                
            # Datos del adjunto
            data = {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": name,
                "contentBytes": content_bytes,
                "isInline": is_inline
            }
            if content_type:
                data["contentType"] = content_type
            
            # Headers
            headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Type': 'application/json'
            }
            
            # Realizar petición POST
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                
                logger.info(f"Adjunto '{name}' agregado exitosamente")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Mail.ReadWrite"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Mail.ReadWrite"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para agregar adjuntos. Se requiere Mail.ReadWrite"
                ) from e
            elif e.response.status_code == 404:
                logger.error("Error 404: Mensaje no encontrado")
                raise ValueError(
                    "El mensaje especificado no existe"
                ) from e
            elif e.response.status_code == 413:
                logger.error("Error 413: Contenido demasiado grande")
                raise ValueError(
                    "El adjunto excede el límite permitido de 3MB"
                ) from e
            raise  # Re-lanza otros errores HTTP
    
    def _process_recipients(self, recipients: list) -> list[dict]:
        """
        Procesa una lista de destinatarios en diferentes formatos y los convierte al formato requerido.
        
        Args:
            recipients (list): Lista de destinatarios en cualquiera de estos formatos:
                - string (email): "user@domain.com"
                - tuple (email, name): ("user@domain.com", "User Name")
                - dict: {"address": "user@domain.com", "name": "User Name"}
                - dict: {"emailAddress": {"address": "user@domain.com", "name": "User Name"}}
                
        Returns:
            list[dict]: Lista de destinatarios en formato Graph API
            
        Examples:
            >>> _process_recipients(["user@domain.com"])
            >>> _process_recipients([("user@domain.com", "User Name")])
            >>> _process_recipients([{"address": "user@domain.com", "name": "User Name"}])
        """
        processed = []
        
        for recipient in recipients:
            if isinstance(recipient, str):
                # Solo email: "user@domain.com"
                processed.append({
                    "emailAddress": {
                        "address": recipient,
                        "name": ""
                    }
                })
            elif isinstance(recipient, tuple):
                # Tupla (email, name)
                email, name = recipient if len(recipient) > 1 else (recipient[0], "")
                processed.append({
                    "emailAddress": {
                        "address": email,
                        "name": name
                    }
                })
            elif isinstance(recipient, dict):
                if "emailAddress" in recipient:
                    # Ya está en formato correcto
                    processed.append(recipient)
                else:
                    # Formato simplificado {"address": "...", "name": "..."}
                    processed.append({
                        "emailAddress": {
                            "address": recipient.get("address"),
                            "name": recipient.get("name", "")
                        }
                    })
            else:
                raise ValueError(
                    f"Formato de destinatario no soportado: {recipient}. "
                    "Use string, tuple o dict"
                )
                
        return processed
    
    
class Mails:
    """Clase para manejar operaciones síncronas relacionadas con correos en Microsoft Graph"""
    
    def __init__(self, client):
        self.client = client

    def list_messages(
        self,
        user_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        select: Optional[str] = None,
        filter: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        body_type: Optional[str] = None
    ) -> dict:
        """
        Lista los mensajes del buzón de un usuario.
        
        Args:
            user_id (str, optional): ID o userPrincipalName del usuario
            folder_id (str, optional): ID de la carpeta específica
            select (str, optional): Propiedades específicas a retornar
            filter (str, optional): Filtro OData
            orderby (str, optional): Ordenamiento OData
            top (int, optional): Número máximo de mensajes (1-1000)
            body_type (str, optional): Formato del cuerpo ('text' o 'html')
            
        Returns:
            dict: Lista de mensajes y nextLink para paginación
        """
        try:
            if not self.client.token:
                self.client.get_token()
                
            # Validaciones igual que en AsyncMails
            if not user_id and not self.client.is_delegated:
                raise ValueError(
                    "Debe proporcionar user_id cuando usa client credentials. "
                    "Para acceder a /me use autenticación delegada"
                )
                
            if top is not None and not (1 <= top <= 1000):
                raise ValueError("top debe estar entre 1 y 1000")
                
            if body_type and body_type not in ['text', 'html']:
                raise ValueError("body_type debe ser 'text' o 'html'")
                
            # Construir URL
            if user_id:
                base_url = f"{self.client.base_url}/users/{user_id}"
            else:
                base_url = f"{self.client.base_url}/me"
                
            if folder_id:
                url = f"{base_url}/mailFolders/{folder_id}/messages"
            else:
                url = f"{base_url}/messages"
                
            # Parámetros y headers igual que AsyncMails
            params = {}
            if select:
                params['$select'] = select
            if filter:
                params['$filter'] = filter
            if orderby:
                params['$orderby'] = orderby
            if top:
                params['$top'] = str(top)
                
            headers = {
                'Authorization': f'Bearer {self.client.token}'
            }
            if body_type:
                headers['Prefer'] = f'outlook.body-content-type="{body_type}"'
                
            # Realizar petición GET síncrona
            with httpx.Client() as client:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                logger.info(
                    f"Mensajes listados exitosamente "
                    f"({len(response.json()['value'])} mensajes)"
                )
                return response.json()
                
        except httpx.HTTPStatusError as e:
            # Manejo de errores igual que AsyncMails
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "InefficientFilter" in e.response.text:
                    raise ValueError(
                        "La combinación de filter y orderby es inválida. "
                        "Asegúrese que las propiedades en orderby:"
                        "\n- También aparezcan en filter"
                        "\n- Estén en el mismo orden que en filter"
                        "\n- Aparezcan antes que otras propiedades en filter"
                    ) from e
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Mail.ReadBasic o Mail.Read"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Mail.ReadBasic o Mail.Read"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para listar mensajes. "
                    "Se requiere Mail.ReadBasic o Mail.Read"
                ) from e
            elif e.response.status_code == 504:
                logger.error("Error 504: Tiempo de espera agotado")
                raise TimeoutError(
                    "La operación tardó demasiado. "
                    "Intente reducir el número de propiedades (select) o mensajes (top)"
                ) from e
            raise

    def add_attachment(
        self,
        message_id: str,
        file_path: Optional[str] = None,
        content: Optional[bytes] = None,
        file_name: Optional[str] = None,
        user_id: Optional[str] = None,
        is_inline: bool = False,
        content_type: Optional[str] = None,
    ) -> dict:
        """
        Agrega un archivo adjunto a un mensaje de forma simplificada.
        
        Args:
            message_id (str): ID del mensaje
            file_path (str, optional): Ruta al archivo que se quiere adjuntar
            content (bytes, optional): Contenido del archivo en bytes
            file_name (str, optional): Nombre del archivo cuando se usa content
            user_id (str, optional): ID o userPrincipalName del usuario
            is_inline (bool): Si el adjunto debe mostrarse en línea en el mensaje
            content_type (str, optional): Tipo MIME del contenido
            
        Returns:
            dict: Información del adjunto creado
            
        Raises:
            ValueError: Si no se proporciona file_path o content+file_name
            FileNotFoundError: Si no se encuentra el archivo
            
        Example:
            # Usando ruta de archivo
            >>> mails.add_attachment(
            ...     message_id="123",
            ...     file_path="documento.pdf"
            ... )
            
            # Usando bytes
            >>> with open('documento.pdf', 'rb') as f:
            ...     content = f.read()
            >>> mails.add_attachment(
            ...     message_id="123",
            ...     content=content,
            ...     file_name="documento.pdf"
            ... )
        """
        # Validar que se proporcione al menos una forma de contenido
        if file_path is None and (content is None or file_name is None):
            raise ValueError(
                "Debe proporcionar file_path o la combinación de content y file_name"
            )
        if file_path is not None and (content is not None or file_name is not None):
            raise ValueError(
                "No puede proporcionar file_path junto con content o file_name"
            )

        try:
            # Caso 1: Usando file_path
            if file_path:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
                
                # Obtener tamaño y tipo del archivo
                file_size = os.path.getsize(file_path)
                if not content_type:
                    content_type, _ = mimetypes.guess_type(file_path)
                    if not content_type:
                        content_type = 'application/octet-stream'
                
                # Obtener nombre del archivo
                file_name = os.path.basename(file_path)
                
                # Leer contenido
                with open(file_path, 'rb') as f:
                    content = f.read()

            # Caso 2: Usando content+filename
            else:
                file_size = len(content)
                if not content_type:
                    content_type, _ = mimetypes.guess_type(file_name)
                    if not content_type:
                        content_type = 'application/octet-stream'

            # Para archivos pequeños (<3MB) usar carga directa
            if file_size <= 3 * 1024 * 1024:
                encoded_content = base64.b64encode(content).decode()
                return self._add_attachment_raw(
                    message_id=message_id,
                    name=file_name,
                    content_bytes=encoded_content,
                    user_id=user_id,
                    is_inline=is_inline,
                    content_type=content_type
                )
            
            # Para archivos grandes usar sesión de carga
            if file_size > 150 * 1024 * 1024:  # 150MB
                raise ValueError("El archivo excede el límite máximo de 150MB")
            
            session = self._create_upload_session(
                message_id=message_id,
                name=file_name,
                size=file_size,
                user_id=user_id,
                is_inline=is_inline
            )
            
            # Subir por chunks
            chunk_size = 4 * 1024 * 1024  # 4MB por chunk
            for start in range(0, file_size, chunk_size):
                chunk = content[start:start + chunk_size]
                end = start + len(chunk) - 1
                
                self._upload_chunk(
                    upload_url=session['uploadUrl'],
                    chunk=chunk,
                    start=start,
                    end=end,
                    total=file_size
                )
            
            logger.info(f"Adjunto '{file_name}' agregado exitosamente")
            return session
            
        except Exception as e:
            logger.error(f"Error al agregar adjunto: {str(e)}")
            raise

    def _create_upload_session(
        self,
        message_id: str,
        name: str,
        size: int,
        user_id: Optional[str] = None,
        is_inline: bool = False
    ) -> dict:
        """Crea una sesión de carga para subir un archivo grande"""
        if not self.client.token:
            self.client.get_token()
        
        # Construir URL
        base_url = f"{self.client.base_url}/users/{user_id}" if user_id else f"{self.client.base_url}/me"
        url = f"{base_url}/messages/{message_id}/attachments/createUploadSession"
        
        # Datos de la sesión
        data = {
            "AttachmentItem": {
                "attachmentType": "file",
                "name": name,
                "size": size,
                "isInline": is_inline
            }
        }
        
        # Crear sesión
        with httpx.Client() as client:
            response = client.post(
                url,
                json=data,
                headers={'Authorization': f'Bearer {self.client.token}'}
            )
            response.raise_for_status()
            return response.json()

    def _upload_chunk(
        self,
        upload_url: str,
        chunk: bytes,
        start: int,
        end: int,
        total: int
    ) -> None:
        """Sube un rango de bytes usando la sesión de carga"""
        headers = {
            'Content-Length': str(len(chunk)),
            'Content-Range': f'bytes {start}-{end}/{total}'
        }
        
        with httpx.Client() as client:
            response = client.put(upload_url, content=chunk, headers=headers)
            response.raise_for_status()

    def _add_attachment_raw(
        self,
        message_id: str,
        name: str,
        content_bytes: str,
        user_id: Optional[str] = None,
        is_inline: bool = False,
        content_type: Optional[str] = None,
    ) -> dict:
        """Método interno que maneja la lógica original de add_attachment"""
        try:
            if not self.client.token:
                self.client.get_token()
                
            # Validar que se proporcione user_id con client credentials
            if not user_id and not self.client.is_delegated:
                raise ValueError(
                    "Debe proporcionar user_id cuando usa client credentials. "
                    "Para acceder a /me use autenticación delegada"
                )
                
            # Validar parámetros
            if not message_id:
                raise ValueError("Debe proporcionar message_id")
                
            # Validar tamaño del adjunto
            if content_bytes and len(content_bytes) > 3 * 1024 * 1024:  # 3MB
                raise ValueError("El adjunto excede el límite de 3MB")
                
            # Construir URL base
            if user_id:
                base_url = f"{self.client.base_url}/users/{user_id}"
            else:
                base_url = f"{self.client.base_url}/me"
                
            # Construir URL final
            url = f"{base_url}/messages/{message_id}/attachments"
                
            # Datos del adjunto
            data = {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": name,
                "contentBytes": content_bytes,
                "isInline": is_inline
            }
            if content_type:
                data["contentType"] = content_type
            
            # Headers
            headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Type': 'application/json'
            }
            
            # Realizar petición POST síncrona
            with httpx.Client() as client:
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()
                
                logger.info(f"Adjunto '{name}' agregado exitosamente")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            # Manejo de errores igual que AsyncMails
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Mail.ReadWrite"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Mail.ReadWrite"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para agregar adjuntos. Se requiere Mail.ReadWrite"
                ) from e
            elif e.response.status_code == 404:
                logger.error("Error 404: Mensaje no encontrado")
                raise ValueError(
                    "El mensaje especificado no existe"
                ) from e
            elif e.response.status_code == 413:
                logger.error("Error 413: Contenido demasiado grande")
                raise ValueError(
                    "El adjunto excede el límite permitido de 3MB"
                ) from e
            raise

    def create_message(
        self,
        subject: str,
        body: str,
        to_recipients: list,
        user_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        body_type: str = "HTML",
        importance: str = "normal",
        cc_recipients: Optional[list] = None,
        bcc_recipients: Optional[list] = None,
        reply_to: Optional[list] = None,
        message_headers: Optional[list[dict]] = None,
        mime_content: Optional[str] = None
    ) -> dict:
        """
        Crea un borrador de mensaje nuevo.
        
        Args:
            subject (str): Asunto del mensaje
            body (str): Contenido del mensaje
            to_recipients (list): Lista de destinatarios en formatos flexibles:
                - ["user@domain.com"]
                - [("user@domain.com", "User Name")]
                - [{"address": "user@domain.com", "name": "User Name"}]
            user_id (str, optional): ID o userPrincipalName del usuario
            folder_id (str, optional): ID de la carpeta donde crear el borrador
            body_type (str): Tipo de contenido del cuerpo ('HTML' o 'text')
            importance (str): Importancia del mensaje ('low', 'normal', 'high')
            cc_recipients (list, optional): Lista de destinatarios en copia
            bcc_recipients (list, optional): Lista de destinatarios en copia oculta
            reply_to (list, optional): Lista de direcciones de respuesta
            message_headers (list[dict], optional): Headers personalizados del mensaje
            mime_content (str, optional): Contenido MIME codificado en base64
        """
        try:
            if not self.client.token:
                self.client.get_token()
                
            # Validaciones igual que AsyncMails
            if not user_id and not self.client.is_delegated:
                raise ValueError(
                    "Debe proporcionar user_id cuando usa client credentials. "
                    "Para acceder a /me use autenticación delegada"
                )
                
            if mime_content:
                if any([body, subject, to_recipients, message_headers]):
                    raise ValueError(
                        "Cuando se proporciona mime_content no se pueden usar "
                        "otros parámetros del mensaje"
                    )
            else:
                if not all([subject, body, to_recipients]):
                    raise ValueError(
                        "Debe proporcionar subject, body y to_recipients"
                    )
                if body_type.upper() not in ['HTML', 'TEXT']:
                    raise ValueError("body_type debe ser 'HTML' o 'text'")
                if importance.lower() not in ['low', 'normal', 'high']:
                    raise ValueError("importance debe ser 'low', 'normal' o 'high'")
                
            # Construir URL
            if user_id:
                base_url = f"{self.client.base_url}/users/{user_id}"
            else:
                base_url = f"{self.client.base_url}/me"
                
            if folder_id:
                url = f"{base_url}/mailFolders/{folder_id}/messages"
            else:
                url = f"{base_url}/messages"
                
            # Headers
            request_headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Type': 'text/plain' if mime_content else 'application/json'
            }
            
            # Datos del mensaje
            if mime_content:
                data = mime_content
            else:
                data = {
                    "subject": subject,
                    "importance": importance.lower(),
                    "body": {
                        "contentType": body_type.lower(),
                        "content": body
                    },
                    "toRecipients": self._process_recipients(to_recipients)
                }
                
                if cc_recipients:
                    data["ccRecipients"] = self._process_recipients(cc_recipients)
                if bcc_recipients:
                    data["bccRecipients"] = self._process_recipients(bcc_recipients)
                if reply_to:
                    data["replyTo"] = self._process_recipients(reply_to)
                    
            if message_headers and len(message_headers) > 0:
                for header in message_headers:
                    if not isinstance(header, dict) or 'name' not in header or 'value' not in header:
                        raise ValueError(
                            "Formato inválido de message_headers. Debe ser: "
                            '[{"name": "x-custom-header", "value": "custom value"}]'
                        )
                data["internetMessageHeaders"] = message_headers
            
            # Realizar petición POST síncrona
            with httpx.Client() as client:
                response = client.post(
                    url, 
                    content=data if mime_content else None,
                    json=data if not mime_content else None,
                    headers=request_headers
                )
                response.raise_for_status()
                
                logger.info(f"Borrador creado exitosamente")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            # Manejo de errores igual que AsyncMails
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "Invalid base64 string" in e.response.text:
                    raise ValueError(
                        "El contenido MIME proporcionado no es una cadena base64 válida"
                    ) from e
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Mail.ReadWrite"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Mail.ReadWrite"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para crear mensajes. Se requiere Mail.ReadWrite"
                ) from e
            elif e.response.status_code == 413:
                logger.error("Error 413: Contenido demasiado grande")
                raise ValueError(
                    "El contenido MIME excede el límite de 4MB"
                ) from e
            raise

    def send_message(
        self,
        message_id: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        Envía un mensaje en borrador existente.
        
        Args:
            message_id (str): ID del mensaje en borrador
            user_id (str, optional): ID o userPrincipalName del usuario
            
        Raises:
            ValueError: Si no se proporciona message_id
            PermissionError: Si no se tienen los permisos necesarios
            
        Example:
            >>> mails.send_message(
            ...     message_id="123",
            ...     user_id="user@domain.com"
            ... )
        """
        try:
            if not self.client.token:
                self.client.get_token()
                
            # Validaciones
            if not user_id and not self.client.is_delegated:
                raise ValueError(
                    "Debe proporcionar user_id cuando usa client credentials. "
                    "Para acceder a /me use autenticación delegada"
                )
                
            if not message_id:
                raise ValueError("Debe proporcionar message_id")
                
            # Construir URL
            if user_id:
                base_url = f"{self.client.base_url}/users/{user_id}"
            else:
                base_url = f"{self.client.base_url}/me"
                
            url = f"{base_url}/messages/{message_id}/send"
                
            # Headers
            headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Length': '0'
            }
            
            # Realizar petición POST síncrona
            with httpx.Client() as client:
                response = client.post(url, headers=headers)
                
                if response.status_code == 202:
                    logger.info("Mensaje enviado exitosamente")
                    return
                    
                response.raise_for_status()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Mail.Send"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Mail.Send"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para enviar mensajes. Se requiere Mail.Send"
                ) from e
            elif e.response.status_code == 404:
                logger.error("Error 404: Mensaje no encontrado")
                raise ValueError(
                    "El mensaje especificado no existe o no es un borrador"
                ) from e
            raise

    def _process_recipients(self, recipients: list) -> list[dict]:
        """
        Procesa una lista de destinatarios en diferentes formatos y los convierte al formato requerido.
        
        Args:
            recipients (list): Lista de destinatarios en cualquiera de estos formatos:
                - string (email): "user@domain.com"
                - tuple (email, name): ("user@domain.com", "User Name")
                - dict: {"address": "user@domain.com", "name": "User Name"}
                - dict: {"emailAddress": {"address": "user@domain.com", "name": "User Name"}}
        """
        processed = []
        
        for recipient in recipients:
            if isinstance(recipient, str):
                processed.append({
                    "emailAddress": {
                        "address": recipient,
                        "name": ""
                    }
                })
            elif isinstance(recipient, tuple):
                email, name = recipient if len(recipient) > 1 else (recipient[0], "")
                processed.append({
                    "emailAddress": {
                        "address": email,
                        "name": name
                    }
                })
            elif isinstance(recipient, dict):
                if "emailAddress" in recipient:
                    processed.append(recipient)
                else:
                    processed.append({
                        "emailAddress": {
                            "address": recipient.get("address"),
                            "name": recipient.get("name", "")
                        }
                    })
            else:
                raise ValueError(
                    f"Formato de destinatario no soportado: {recipient}. "
                    "Use string, tuple o dict"
                )
                
        return processed
    