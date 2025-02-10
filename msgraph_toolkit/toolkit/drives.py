from typing import Optional
import httpx
from ..core.log import Log

logger = Log(__name__)

class AsyncDrives:
    """Clase para manejar operaciones relacionadas con drives en Microsoft Graph"""
    
    def __init__(self, client):
        self.client = client
        
    async def list_drives(
        self,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        select: Optional[str] = None
    ) -> dict:
        """
        Lista las unidades (drives) disponibles para un usuario, grupo o sitio.
        
        Args:
            user_id (str, optional): ID del usuario para listar sus drives
            resource_id (str, optional): ID del recurso (usuario, grupo o sitio)
            resource_type (str, optional): Tipo de recurso ('users', 'groups', 'sites')
            select (str, optional): Propiedades específicas a retornar
            
        Returns:
            dict: Lista de unidades disponibles
            
        Raises:
            ValueError: Si la combinación de resource_id y resource_type no es válida
        """
        if not self.client.token:
            await self.client.get_token()
            
        # Construir URL base según el tipo de recurso
        if resource_id and resource_type:
            if resource_type not in ['users', 'groups', 'sites']:
                raise ValueError("resource_type debe ser 'users', 'groups' o 'sites'")
            url = f"{self.client.base_url}/{resource_type}/{resource_id}/drives"
        else:
            # Si no se especifica recurso, lista las unidades del usuario actual
            url = f"{self.client.base_url}/users/{user_id}/drives"
            
        # Parámetros de consulta
        params = {}
        if select:
            params['$select'] = select
            
        # Headers
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        # Realizar petición GET
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Unidades listadas exitosamente")
            return response.json()

    async def get_drive(
        self,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        select: Optional[str] = None
    ) -> dict:
        """
        Obtiene información detallada de una unidad (drive).
        
        Args:
            drive_id (str, optional): ID único del drive
            user_id (str, optional): ID o userPrincipalName del usuario para obtener su OneDrive
            group_id (str, optional): ID del grupo para obtener su biblioteca de documentos
            site_id (str, optional): ID del sitio para obtener su biblioteca de documentos
            select (str, optional): Propiedades específicas a retornar
            
        Returns:
            dict: Información del drive
            
        Raises:
            ValueError: Si no se proporciona ningún ID o si se proporcionan múltiples IDs
            Exception: Si hay error en la petición
        """
        if not self.client.token:
            await self.client.get_token()
            
        # Validar que solo se proporcione un tipo de ID
        ids = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
        if len(ids) == 0:
            raise ValueError("Debe proporcionar drive_id, user_id, group_id o site_id")
        if len(ids) > 1:
            raise ValueError("Solo puede proporcionar un tipo de ID")
            
        # Construir URL según el tipo de ID proporcionado
        if drive_id:
            url = f"{self.client.base_url}/drives/{drive_id}"
        elif user_id:
            url = f"{self.client.base_url}/users/{user_id}/drive"
        elif group_id:
            url = f"{self.client.base_url}/groups/{group_id}/drive"
        elif site_id:
            url = f"{self.client.base_url}/sites/{site_id}/drive"
            
        # Parámetros de consulta
        params = {}
        if select:
            params['$select'] = select
            
        # Headers
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        # Realizar petición GET
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Drive obtenido exitosamente")
            return response.json()

    async def get_item(
        self,
        item_id: Optional[str] = None,
        item_path: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        list_id: Optional[str] = None,
        select: Optional[str] = None,
        expand: Optional[str] = None,
        include_deleted: bool = False,
        etag: Optional[str] = None
    ) -> dict:
        """
        Obtiene metadata de un elemento (driveItem) en un drive por ID o ruta.
        
        Args:
            item_id (str, optional): ID del elemento
            item_path (str, optional): Ruta del elemento (ej: '/documentos/archivo.pdf')
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            list_id (str, optional): ID de la lista (solo para SharePoint)
            select (str, optional): Propiedades específicas a retornar
            expand (str, optional): Relaciones a expandir (ej: 'children')
            include_deleted (bool): Si se deben incluir elementos eliminados
            etag (str, optional): ETag para validación condicional
            
        Returns:
            dict: Metadata del elemento
            
        Raises:
            ValueError: Si la combinación de parámetros no es válida
            HTTPStatusError: Si hay error en la petición o el recurso no ha sido modificado (304)
        """
        if not self.client.token:
            await self.client.get_token()
            
        # Validar que solo se use un tipo de identificador de drive
        drive_identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
        if len(drive_identifiers) > 1:
            raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
            
        # Validar que no se usen item_id e item_path simultáneamente
        if item_id is not None and item_path is not None:
            raise ValueError("No puede proporcionar item_id e item_path simultáneamente")
            
        # Construir URL base
        if drive_id:
            base_url = f"{self.client.base_url}/drives/{drive_id}"
        elif user_id:
            base_url = f"{self.client.base_url}/users/{user_id}/drive"
        elif group_id:
            base_url = f"{self.client.base_url}/groups/{group_id}/drive"
        elif site_id:
            if list_id:
                # Caso especial para listas de SharePoint
                url = f"{self.client.base_url}/sites/{site_id}/lists/{list_id}/items/{item_id}/driveItem"
                item_path = None  # No se usa path en este caso
            else:
                base_url = f"{self.client.base_url}/sites/{site_id}/drive"
        else:
            base_url = f"{self.client.base_url}/me/drive"
            
        # Construir URL final
        if item_path is not None:
            url = f"{base_url}/root:/{item_path.strip('/')}"
        elif item_id is not None and not list_id:  # list_id ya tiene URL completa
            url = f"{base_url}/items/{item_id}"
        else:
            url = f"{base_url}/root"  # Obtener raíz si no se especifica item
            
        # Parámetros de consulta
        params = {}
        if select:
            params['$select'] = select
        if expand:
            params['$expand'] = expand
        if include_deleted and item_id:  # Solo válido con item_id
            params['includeDeletedItems'] = 'true'
            
        # Headers
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        if etag:
            headers['if-none-match'] = etag
            
        # Realizar petición GET
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            
            # Manejar 304 Not Modified
            if response.status_code == 304:
                logger.info("El elemento no ha sido modificado")
                return None
                
            response.raise_for_status()
            logger.info(f"Elemento obtenido exitosamente")
            return response.json()

    async def list_followed(
        self,
        user_id: Optional[str] = None,
        select: Optional[str] = None
    ) -> dict:
        """
        Lista los elementos que han sido seguidos por un usuario.
        Incluye elementos en el drive del usuario y elementos a los que tiene acceso en otros drives.
        
        Args:
            user_id (str, optional): ID del usuario. Si no se proporciona, se usa el usuario actual
            select (str, optional): Propiedades específicas a retornar
            
        Returns:
            dict: Lista de elementos seguidos
            
        Raises:
            Exception: Si hay error en la petición
            
        Note:
            - No soportado para cuentas personales de Microsoft
            - Requiere permisos Files.Read o Files.Read.All
        """
        if not self.client.token:
            await self.client.get_token()
            
        # Construir URL
        if user_id:
            url = f"{self.client.base_url}/users/{user_id}/drive/following"
        else:
            url = f"{self.client.base_url}/me/drive/following"
            
        # Parámetros de consulta
        params = {}
        if select:
            params['$select'] = select
            
        # Headers
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        # Realizar petición GET
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Elementos seguidos listados exitosamente")
            return response.json()

    async def list_items(
        self,
        item_id: Optional[str] = None,
        item_path: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        select: Optional[str] = None,
        expand: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None
    ) -> dict:
        """
        Lista los elementos hijos (children) de un DriveItem.
        Si no se proporciona item_id o item_path, lista los elementos en la raíz del drive.
        
        Args:
            item_id (str, optional): ID del elemento padre
            item_path (str, optional): Ruta del elemento padre
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            select (str, optional): Propiedades específicas a retornar
            expand (str, optional): Relaciones a expandir
            orderby (str, optional): Campo para ordenar resultados
            top (int, optional): Número máximo de elementos a retornar
            
        Returns:
            dict: Lista de elementos hijos
            
        Raises:
            ValueError: Si se proporciona una combinación inválida de parámetros
        """
        if not self.client.token:
            await self.client.get_token()
            
        # Validar que solo se use un tipo de identificador de drive
        drive_identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
        if len(drive_identifiers) > 1:
            raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
            
        # Validar que no se usen item_id e item_path simultáneamente
        if item_id is not None and item_path is not None:
            raise ValueError("No puede proporcionar item_id e item_path simultáneamente")
            
        # Construir URL base
        if drive_id:
            base_url = f"{self.client.base_url}/drives/{drive_id}"
        elif user_id:
            base_url = f"{self.client.base_url}/users/{user_id}/drive"
        elif group_id:
            base_url = f"{self.client.base_url}/groups/{group_id}/drive"
        elif site_id:
            base_url = f"{self.client.base_url}/sites/{site_id}/drive"
        else:
            base_url = f"{self.client.base_url}/me/drive"
            
        # Construir URL final
        if item_path is not None:
            url = f"{base_url}/root:/{item_path.strip('/')}:/children"
        elif item_id is not None:
            if item_id == 'root':
                url = f"{base_url}/root/children"
            else:
                url = f"{base_url}/items/{item_id}/children"
        else:
            url = f"{base_url}/root/children"
            
        # Parámetros de consulta
        params = {}
        if select:
            params['$select'] = select
        if expand:
            params['$expand'] = expand
        if orderby:
            params['$orderby'] = orderby
        if top:
            params['$top'] = str(top)
            
        # Headers
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        # Realizar petición GET
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Elementos hijos listados exitosamente")
            return response.json()

    async def list_changes(
        self,
        token: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        select: Optional[str] = None,
        expand: Optional[str] = None,
        top: Optional[int] = None,
        show_sharing_changes: bool = False
    ) -> dict:
        """
        Rastrea cambios en un DriveItem y sus hijos a lo largo del tiempo.
        
        Args:
            token (str, optional): Token delta previo o 'latest' para obtener el último token
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            select (str, optional): Propiedades específicas a retornar
            expand (str, optional): Relaciones a expandir
            top (int, optional): Número máximo de elementos a retornar
            show_sharing_changes (bool): Si se deben mostrar cambios en permisos
            
        Returns:
            dict: Lista de cambios y token delta para la siguiente consulta
            
        Note:
            - Si no se especifica token, enumera el estado actual de la jerarquía
            - Si token='latest', retorna respuesta vacía con el último token delta
            - Si se proporciona un token delta previo, retorna cambios desde ese token
        """
        if not self.client.token:
            await self.client.get_token()
            
        # Validar que solo se use un tipo de identificador de drive
        drive_identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
        if len(drive_identifiers) > 1:
            raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
            
        # Construir URL base
        if drive_id:
            base_url = f"{self.client.base_url}/drives/{drive_id}"
        elif user_id:
            base_url = f"{self.client.base_url}/users/{user_id}/drive"
        elif group_id:
            base_url = f"{self.client.base_url}/groups/{group_id}/drive"
        elif site_id:
            base_url = f"{self.client.base_url}/sites/{site_id}/drive"
        else:
            base_url = f"{self.client.base_url}/me/drive"
            
        # Construir URL final
        url = f"{base_url}/root/delta"
        if token:
            url += f"(token='{token}')" if token != 'latest' else "?token=latest"
            
        # Parámetros de consulta
        params = {}
        if select:
            params['$select'] = select
        if expand:
            params['$expand'] = expand
        if top:
            params['$top'] = str(top)
            
        # Headers
        headers = {
            'Authorization': f'Bearer {self.client.token}',
            'Prefer': 'hierarchicalsharing'
        }
        
        if show_sharing_changes:
            headers['Prefer'] = 'deltashowremovedasdeleted, deltatraversepermissiongaps, deltashowsharingchanges'
            
        # Realizar petición GET
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Cambios delta obtenidos exitosamente")
            return response.json()

    async def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        conflict_behavior: str = "rename"
    ) -> dict:
        """
        Crea una nueva carpeta en un drive.
        
        Args:
            name (str): Nombre de la carpeta a crear
            parent_id (str, optional): ID de la carpeta padre. Si no se proporciona, se crea en la raíz
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            conflict_behavior (str, optional): Comportamiento en caso de conflicto ('rename', 'replace', 'fail')
            
        Returns:
            dict: Información de la carpeta creada
            
        Raises:
            ValueError: Si la combinación de parámetros no es válida
            HTTPStatusError: Si hay error en la petición
            PermissionError: Si no se tienen los permisos necesarios (Files.ReadWrite o Files.ReadWrite.All)
        """
        try:
            if not self.client.token:
                await self.client.get_token()
                
            # Validar que se proporcione al menos un identificador
            identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
            if len(identifiers) == 0:
                raise ValueError("Debe proporcionar uno de: drive_id, user_id, group_id, site_id")
            if len(identifiers) > 1:
                raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
                
            # Validar conflict_behavior
            if conflict_behavior not in ['rename', 'replace', 'fail']:
                raise ValueError("conflict_behavior debe ser 'rename', 'replace' o 'fail'")
                
            # Construir URL base
            if drive_id:
                base_url = f"{self.client.base_url}/drives/{drive_id}"
            elif user_id:
                base_url = f"{self.client.base_url}/users/{user_id}/drive"
            elif group_id:
                base_url = f"{self.client.base_url}/groups/{group_id}/drive"
            elif site_id:
                base_url = f"{self.client.base_url}/sites/{site_id}/drive"
            else:
                raise ValueError("Debe proporcionar uno de: drive_id, user_id, group_id, site_id")
                
            # Construir URL final
            if parent_id:
                url = f"{base_url}/items/{parent_id}/children"
            else:
                url = f"{base_url}/root/children"
                
            # Datos de la carpeta a crear
            data = {
                "name": name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": conflict_behavior
            }
                
            # Headers
            headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Type': 'application/json'
            }
            
            # Realizar petición POST
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                
                logger.info(f"Carpeta '{name}' creada exitosamente")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Files.ReadWrite o Files.ReadWrite.All"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para crear carpetas en este drive. " 
                    "Se requiere Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            raise  # Re-lanza otros errores HTTP 

    async def update_item(
        self,
        item_id: str,
        properties: dict,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        etag: Optional[str] = None
    ) -> dict:
        """
        Actualiza las propiedades de un DriveItem.
        
        Args:
            item_id (str): ID del elemento a actualizar
            properties (dict): Propiedades a actualizar (ej: {"name": "nuevo-nombre.docx"})
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            etag (str, optional): ETag para validación condicional
            
        Returns:
            dict: DriveItem actualizado
            
        Raises:
            ValueError: Si la combinación de parámetros no es válida
            HTTPStatusError: Si hay error en la petición
            PermissionError: Si no se tienen los permisos necesarios (Files.ReadWrite o Files.ReadWrite.All)
        """
        try:
            if not self.client.token:
                await self.client.get_token()
                
            # Validar que se proporcione al menos un identificador
            identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
            if len(identifiers) > 1:
                raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
                
            # Construir URL base
            if drive_id:
                base_url = f"{self.client.base_url}/drives/{drive_id}"
            elif user_id:
                base_url = f"{self.client.base_url}/users/{user_id}/drive"
            elif group_id:
                base_url = f"{self.client.base_url}/groups/{group_id}/drive"
            elif site_id:
                base_url = f"{self.client.base_url}/sites/{site_id}/drive"
            else:
                base_url = f"{self.client.base_url}/me/drive"
                
            # Construir URL final
            url = f"{base_url}/items/{item_id}"
                
            # Headers
            headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Type': 'application/json'
            }
            if etag:
                headers['if-match'] = etag
            
            # Realizar petición PATCH
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, json=properties, headers=headers)
                
                # Manejar error de precondición fallida
                if response.status_code == 412:
                    logger.error("Error 412: La versión del elemento ha cambiado")
                    return None
                    
                response.raise_for_status()
                logger.info(f"Elemento actualizado exitosamente")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Files.ReadWrite o Files.ReadWrite.All"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para actualizar elementos en este drive. " 
                    "Se requiere Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            raise  # Re-lanza otros errores HTTP 

    async def upload_content(
        self,
        content: bytes,
        filename: Optional[str] = None,
        item_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        content_type: str = "application/octet-stream"
    ) -> dict:
        """
        Sube o actualiza el contenido de un archivo (hasta 250MB).
        Para archivos más grandes usar upload_large_file.
        
        Args:
            content (bytes): Contenido del archivo en bytes
            filename (str, optional): Nombre del archivo nuevo
            item_id (str, optional): ID del archivo a actualizar
            parent_id (str, optional): ID de la carpeta donde crear el archivo
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            content_type (str, optional): Tipo MIME del contenido
            
        Returns:
            dict: DriveItem del archivo creado o actualizado
            
        Raises:
            ValueError: Si la combinación de parámetros no es válida
            HTTPStatusError: Si hay error en la petición
            PermissionError: Si no se tienen los permisos necesarios
            
        Note:
            - Para crear un archivo nuevo: proporcionar filename y parent_id
            - Para actualizar un archivo: proporcionar item_id
        """
        try:
            if not self.client.token:
                await self.client.get_token()
                
            # Validar tamaño del archivo
            if len(content) > 250 * 1024 * 1024:  # 250MB
                raise ValueError(
                    "El archivo excede el límite de 250MB. "
                    "Use upload_large_file para archivos más grandes"
                )
                
            # Validar que se proporcione al menos un identificador
            identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
            if len(identifiers) > 1:
                raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
                
            # Validar modo de operación
            if item_id:
                if filename or parent_id:
                    raise ValueError(
                        "Para actualizar un archivo use solo item_id. "
                        "Para crear uno nuevo use filename y parent_id"
                    )
            else:
                if not filename or not parent_id:
                    raise ValueError(
                        "Para crear un archivo nuevo debe proporcionar filename y parent_id"
                    )
                
            # Construir URL base
            if drive_id:
                base_url = f"{self.client.base_url}/drives/{drive_id}"
            elif user_id:
                base_url = f"{self.client.base_url}/users/{user_id}/drive"
            elif group_id:
                base_url = f"{self.client.base_url}/groups/{group_id}/drive"
            elif site_id:
                base_url = f"{self.client.base_url}/sites/{site_id}/drive"
            else:
                base_url = f"{self.client.base_url}/me/drive"
                
            # Construir URL final
            if item_id:
                # Actualizar archivo existente
                url = f"{base_url}/items/{item_id}/content"
            else:
                # Crear archivo nuevo
                url = f"{base_url}/items/{parent_id}:/{filename}:/content"
                
            # Headers
            headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Type': content_type
            }
            
            # Realizar petición PUT
            async with httpx.AsyncClient() as client:
                response = await client.put(url, content=content, headers=headers)
                response.raise_for_status()
                
                logger.info(
                    f"Archivo {'actualizado' if item_id else 'creado'} exitosamente"
                )
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Files.ReadWrite o Files.ReadWrite.All"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para subir archivos en este drive. " 
                    "Se requiere Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            elif e.response.status_code == 413:
                logger.error("Error 413: Contenido demasiado grande")
                raise ValueError(
                    "El archivo excede el límite permitido. "
                    "Use upload_large_file para archivos más grandes"
                ) from e
            raise  # Re-lanza otros errores HTTP

    async def download_content(
        self,
        item_id: Optional[str] = None,
        item_path: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        etag: Optional[str] = None,
        byte_range: Optional[tuple[int, int]] = None
    ) -> bytes:
        """
        Descarga el contenido de un archivo.
        
        Args:
            item_id (str, optional): ID del archivo
            item_path (str, optional): Ruta del archivo (ej: '/documentos/archivo.pdf')
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            etag (str, optional): ETag para validación condicional
            byte_range (tuple[int, int], optional): Rango de bytes a descargar (inicio, fin)
            
        Returns:
            bytes: Contenido del archivo
            
        Raises:
            ValueError: Si la combinación de parámetros no es válida
            HTTPStatusError: Si hay error en la petición
            PermissionError: Si no se tienen los permisos necesarios
            
        Note:
            - Solo archivos (DriveItems con propiedad file) pueden ser descargados
            - Para archivos grandes considere usar byte_range para descargar por partes
        """
        try:
            if not self.client.token:
                await self.client.get_token()
                
            # Validar que se proporcione al menos un identificador
            identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
            if len(identifiers) > 1:
                raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
                
            # Validar que se proporcione item_id o item_path
            if item_id is None and item_path is None:
                raise ValueError("Debe proporcionar item_id o item_path")
            if item_id is not None and item_path is not None:
                raise ValueError("No puede proporcionar item_id e item_path simultáneamente")
                
            # Construir URL base
            if drive_id:
                base_url = f"{self.client.base_url}/drives/{drive_id}"
            elif user_id:
                base_url = f"{self.client.base_url}/users/{user_id}/drive"
            elif group_id:
                base_url = f"{self.client.base_url}/groups/{group_id}/drive"
            elif site_id:
                base_url = f"{self.client.base_url}/sites/{site_id}/drive"
            else:
                base_url = f"{self.client.base_url}/me/drive"
                
            # Construir URL final
            if item_path is not None:
                url = f"{base_url}/root:/{item_path.strip('/')}:/content"
            else:
                url = f"{base_url}/items/{item_id}/content"
                
            # Headers
            headers = {
                'Authorization': f'Bearer {self.client.token}'
            }
            if etag:
                headers['if-none-match'] = etag
            if byte_range:
                headers['Range'] = f'bytes={byte_range[0]}-{byte_range[1]}'
                
            # Realizar petición GET
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                
                # Manejar 304 Not Modified
                if response.status_code == 304:
                    logger.info("El archivo no ha sido modificado")
                    return None
                    
                response.raise_for_status()
                
                logger.info(
                    f"Archivo descargado exitosamente "
                    f"({len(response.content)} bytes)"
                )
                return response.content
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Files.Read o Files.Read.All"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Files.Read o Files.Read.All"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para descargar archivos de este drive. " 
                    "Se requiere Files.Read o Files.Read.All"
                ) from e
            elif e.response.status_code == 404:
                logger.error("Error 404: Archivo no encontrado")
                raise FileNotFoundError("El archivo solicitado no existe") from e
            raise  # Re-lanza otros errores HTTP

class Drives:
    """Clase para manejar operaciones síncronas relacionadas con drives en Microsoft Graph"""
    
    def __init__(self, client):
        self.client = client
        
    def list_drives(
        self,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        select: Optional[str] = None
    ) -> dict:
        """
        Lista las unidades (drives) disponibles para un usuario, grupo o sitio.
        
        Args:
            user_id (str, optional): ID del usuario para listar sus drives
            resource_id (str, optional): ID del recurso (usuario, grupo o sitio)
            resource_type (str, optional): Tipo de recurso ('users', 'groups', 'sites')
            select (str, optional): Propiedades específicas a retornar
        """
        if not self.client.token:
            self.client.get_token()
            
        # Construir URL base según el tipo de recurso
        if resource_id and resource_type:
            if resource_type not in ['users', 'groups', 'sites']:
                raise ValueError("resource_type debe ser 'users', 'groups' o 'sites'")
            url = f"{self.client.base_url}/{resource_type}/{resource_id}/drives"
        else:
            url = f"{self.client.base_url}/users/{user_id}/drives"
            
        params = {}
        if select:
            params['$select'] = select
            
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        with httpx.Client() as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Unidades listadas exitosamente")
            return response.json()

    def get_drive(
        self,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        select: Optional[str] = None
    ) -> dict:
        """
        Obtiene información detallada de una unidad (drive).
        
        Args:
            drive_id (str, optional): ID único del drive
            user_id (str, optional): ID o userPrincipalName del usuario para obtener su OneDrive
            group_id (str, optional): ID del grupo para obtener su biblioteca de documentos
            site_id (str, optional): ID del sitio para obtener su biblioteca de documentos
            select (str, optional): Propiedades específicas a retornar
        """
        if not self.client.token:
            self.client.get_token()
            
        ids = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
        if len(ids) == 0:
            raise ValueError("Debe proporcionar drive_id, user_id, group_id o site_id")
        if len(ids) > 1:
            raise ValueError("Solo puede proporcionar un tipo de ID")
            
        if drive_id:
            url = f"{self.client.base_url}/drives/{drive_id}"
        elif user_id:
            url = f"{self.client.base_url}/users/{user_id}/drive"
        elif group_id:
            url = f"{self.client.base_url}/groups/{group_id}/drive"
        elif site_id:
            url = f"{self.client.base_url}/sites/{site_id}/drive"
            
        params = {}
        if select:
            params['$select'] = select
            
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        with httpx.Client() as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Drive obtenido exitosamente")
            return response.json()

    def get_item(
        self,
        item_id: Optional[str] = None,
        item_path: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        list_id: Optional[str] = None,
        select: Optional[str] = None,
        expand: Optional[str] = None,
        include_deleted: bool = False,
        etag: Optional[str] = None
    ) -> dict:
        """
        Obtiene metadata de un elemento (driveItem) en un drive por ID o ruta.
        
        Args:
            item_id (str, optional): ID del elemento
            item_path (str, optional): Ruta del elemento (ej: '/documentos/archivo.pdf')
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            list_id (str, optional): ID de la lista (solo para SharePoint)
            select (str, optional): Propiedades específicas a retornar
            expand (str, optional): Relaciones a expandir (ej: 'children')
            include_deleted (bool): Si se deben incluir elementos eliminados
            etag (str, optional): ETag para validación condicional
        """
        if not self.client.token:
            self.client.get_token()
            
        drive_identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
        if len(drive_identifiers) > 1:
            raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
            
        if item_id is not None and item_path is not None:
            raise ValueError("No puede proporcionar item_id e item_path simultáneamente")
            
        if drive_id:
            base_url = f"{self.client.base_url}/drives/{drive_id}"
        elif user_id:
            base_url = f"{self.client.base_url}/users/{user_id}/drive"
        elif group_id:
            base_url = f"{self.client.base_url}/groups/{group_id}/drive"
        elif site_id:
            if list_id:
                url = f"{self.client.base_url}/sites/{site_id}/lists/{list_id}/items/{item_id}/driveItem"
                item_path = None
            else:
                base_url = f"{self.client.base_url}/sites/{site_id}/drive"
        else:
            base_url = f"{self.client.base_url}/me/drive"
            
        if item_path is not None:
            url = f"{base_url}/root:/{item_path.strip('/')}"
        elif item_id is not None and not list_id:
            url = f"{base_url}/items/{item_id}"
        else:
            url = f"{base_url}/root"
            
        params = {}
        if select:
            params['$select'] = select
        if expand:
            params['$expand'] = expand
        if include_deleted and item_id:
            params['includeDeletedItems'] = 'true'
            
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        if etag:
            headers['if-none-match'] = etag
            
        with httpx.Client() as client:
            response = client.get(url, params=params, headers=headers)
            
            if response.status_code == 304:
                logger.info("El elemento no ha sido modificado")
                return None
                
            response.raise_for_status()
            logger.info(f"Elemento obtenido exitosamente")
            return response.json()

    def list_followed(
        self,
        user_id: Optional[str] = None,
        select: Optional[str] = None
    ) -> dict:
        """
        Lista los elementos que han sido seguidos por un usuario.
        Incluye elementos en el drive del usuario y elementos a los que tiene acceso en otros drives.
        
        Args:
            user_id (str, optional): ID del usuario. Si no se proporciona, se usa el usuario actual
            select (str, optional): Propiedades específicas a retornar
        """
        if not self.client.token:
            self.client.get_token()
            
        if user_id:
            url = f"{self.client.base_url}/users/{user_id}/drive/following"
        else:
            url = f"{self.client.base_url}/me/drive/following"
            
        params = {}
        if select:
            params['$select'] = select
            
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        with httpx.Client() as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Elementos seguidos listados exitosamente")
            return response.json()

    def list_items(
        self,
        item_id: Optional[str] = None,
        item_path: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        select: Optional[str] = None,
        expand: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None
    ) -> dict:
        """
        Lista los elementos hijos (children) de un DriveItem.
        Si no se proporciona item_id o item_path, lista los elementos en la raíz del drive.
        
        Args:
            item_id (str, optional): ID del elemento padre
            item_path (str, optional): Ruta del elemento padre
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            select (str, optional): Propiedades específicas a retornar
            expand (str, optional): Relaciones a expandir
            orderby (str, optional): Campo para ordenar resultados
            top (int, optional): Número máximo de elementos a retornar
        """
        if not self.client.token:
            self.client.get_token()
            
        drive_identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
        if len(drive_identifiers) > 1:
            raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
            
        if item_id is not None and item_path is not None:
            raise ValueError("No puede proporcionar item_id e item_path simultáneamente")
            
        if drive_id:
            base_url = f"{self.client.base_url}/drives/{drive_id}"
        elif user_id:
            base_url = f"{self.client.base_url}/users/{user_id}/drive"
        elif group_id:
            base_url = f"{self.client.base_url}/groups/{group_id}/drive"
        elif site_id:
            base_url = f"{self.client.base_url}/sites/{site_id}/drive"
        else:
            base_url = f"{self.client.base_url}/me/drive"
            
        if item_path is not None:
            url = f"{base_url}/root:/{item_path.strip('/')}:/children"
        elif item_id is not None:
            if item_id == 'root':
                url = f"{base_url}/root/children"
            else:
                url = f"{base_url}/items/{item_id}/children"
        else:
            url = f"{base_url}/root/children"
            
        params = {}
        if select:
            params['$select'] = select
        if expand:
            params['$expand'] = expand
        if orderby:
            params['$orderby'] = orderby
        if top:
            params['$top'] = str(top)
            
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        with httpx.Client() as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Elementos hijos listados exitosamente")
            return response.json()

    def list_changes(
        self,
        token: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        select: Optional[str] = None,
        expand: Optional[str] = None,
        top: Optional[int] = None,
        show_sharing_changes: bool = False
    ) -> dict:
        """
        Rastrea cambios en un DriveItem y sus hijos a lo largo del tiempo.
        
        Args:
            token (str, optional): Token delta previo o 'latest' para obtener el último token
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            select (str, optional): Propiedades específicas a retornar
            expand (str, optional): Relaciones a expandir
            top (int, optional): Número máximo de elementos a retornar
            show_sharing_changes (bool): Si se deben mostrar cambios en permisos
        """
        if not self.client.token:
            self.client.get_token()
            
        drive_identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
        if len(drive_identifiers) > 1:
            raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
            
        if drive_id:
            base_url = f"{self.client.base_url}/drives/{drive_id}"
        elif user_id:
            base_url = f"{self.client.base_url}/users/{user_id}/drive"
        elif group_id:
            base_url = f"{self.client.base_url}/groups/{group_id}/drive"
        elif site_id:
            base_url = f"{self.client.base_url}/sites/{site_id}/drive"
        else:
            base_url = f"{self.client.base_url}/me/drive"
            
        url = f"{base_url}/root/delta"
        if token:
            url += f"(token='{token}')" if token != 'latest' else "?token=latest"
            
        params = {}
        if select:
            params['$select'] = select
        if expand:
            params['$expand'] = expand
        if top:
            params['$top'] = str(top)
            
        headers = {
            'Authorization': f'Bearer {self.client.token}',
            'Prefer': 'hierarchicalsharing'
        }
        
        if show_sharing_changes:
            headers['Prefer'] = 'deltashowremovedasdeleted, deltatraversepermissiongaps, deltashowsharingchanges'
            
        with httpx.Client() as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Cambios delta obtenidos exitosamente")
            return response.json()

    def update_item(
        self,
        item_id: str,
        properties: dict,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        etag: Optional[str] = None
    ) -> dict:
        """
        Actualiza las propiedades de un DriveItem.
        
        Args:
            item_id (str): ID del elemento a actualizar
            properties (dict): Propiedades a actualizar
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            etag (str, optional): ETag para validación condicional
            
        Returns:
            dict: DriveItem actualizado
        """
        try:
            if not self.client.token:
                self.client.get_token()
                
            identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
            if len(identifiers) > 1:
                raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
                
            if drive_id:
                base_url = f"{self.client.base_url}/drives/{drive_id}"
            elif user_id:
                base_url = f"{self.client.base_url}/users/{user_id}/drive"
            elif group_id:
                base_url = f"{self.client.base_url}/groups/{group_id}/drive"
            elif site_id:
                base_url = f"{self.client.base_url}/sites/{site_id}/drive"
            else:
                base_url = f"{self.client.base_url}/me/drive"
                
            url = f"{base_url}/items/{item_id}"
                
            headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Type': 'application/json'
            }
            if etag:
                headers['if-match'] = etag
            
            with httpx.Client() as client:
                response = client.patch(url, json=properties, headers=headers)
                
                if response.status_code == 412:
                    logger.error("Error 412: La versión del elemento ha cambiado")
                    return None
                    
                response.raise_for_status()
                logger.info(f"Elemento actualizado exitosamente")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Files.ReadWrite o Files.ReadWrite.All"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para actualizar elementos en este drive. " 
                    "Se requiere Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            raise

    def upload_content(
        self,
        content: bytes,
        filename: Optional[str] = None,
        item_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        content_type: str = "application/octet-stream"
    ) -> dict:
        """
        Sube o actualiza el contenido de un archivo (hasta 250MB).
        Para archivos más grandes usar upload_large_file.
        
        Args:
            content (bytes): Contenido del archivo en bytes
            filename (str, optional): Nombre del archivo nuevo
            item_id (str, optional): ID del archivo a actualizar
            parent_id (str, optional): ID de la carpeta donde crear el archivo
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            content_type (str, optional): Tipo MIME del contenido
        """
        try:
            if not self.client.token:
                self.client.get_token()
                
            if len(content) > 250 * 1024 * 1024:  # 250MB
                raise ValueError(
                    "El archivo excede el límite de 250MB. "
                    "Use upload_large_file para archivos más grandes"
                )
                
            identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
            if len(identifiers) > 1:
                raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
                
            if item_id:
                if filename or parent_id:
                    raise ValueError(
                        "Para actualizar un archivo use solo item_id. "
                        "Para crear uno nuevo use filename y parent_id"
                    )
            else:
                if not filename or not parent_id:
                    raise ValueError(
                        "Para crear un archivo nuevo debe proporcionar filename y parent_id"
                    )
                
            if drive_id:
                base_url = f"{self.client.base_url}/drives/{drive_id}"
            elif user_id:
                base_url = f"{self.client.base_url}/users/{user_id}/drive"
            elif group_id:
                base_url = f"{self.client.base_url}/groups/{group_id}/drive"
            elif site_id:
                base_url = f"{self.client.base_url}/sites/{site_id}/drive"
            else:
                base_url = f"{self.client.base_url}/me/drive"
                
            if item_id:
                url = f"{base_url}/items/{item_id}/content"
            else:
                url = f"{base_url}/items/{parent_id}:/{filename}:/content"
                
            headers = {
                'Authorization': f'Bearer {self.client.token}',
                'Content-Type': content_type
            }
            
            with httpx.Client() as client:
                response = client.put(url, content=content, headers=headers)
                response.raise_for_status()
                
                logger.info(
                    f"Archivo {'actualizado' if item_id else 'creado'} exitosamente"
                )
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Files.ReadWrite o Files.ReadWrite.All"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para subir archivos en este drive. " 
                    "Se requiere Files.ReadWrite o Files.ReadWrite.All"
                ) from e
            elif e.response.status_code == 413:
                logger.error("Error 413: Contenido demasiado grande")
                raise ValueError(
                    "El archivo excede el límite permitido. "
                    "Use upload_large_file para archivos más grandes"
                ) from e
            raise

    def download_content(
        self,
        item_id: Optional[str] = None,
        item_path: Optional[str] = None,
        drive_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        site_id: Optional[str] = None,
        etag: Optional[str] = None,
        byte_range: Optional[tuple[int, int]] = None
    ) -> bytes:
        """
        Descarga el contenido de un archivo.
        
        Args:
            item_id (str, optional): ID del archivo
            item_path (str, optional): Ruta del archivo (ej: '/documentos/archivo.pdf')
            drive_id (str, optional): ID del drive
            user_id (str, optional): ID del usuario
            group_id (str, optional): ID del grupo
            site_id (str, optional): ID del sitio
            etag (str, optional): ETag para validación condicional
            byte_range (tuple[int, int], optional): Rango de bytes a descargar (inicio, fin)
        """
        try:
            if not self.client.token:
                self.client.get_token()
                
            identifiers = [i for i in [drive_id, user_id, group_id, site_id] if i is not None]
            if len(identifiers) > 1:
                raise ValueError("Solo puede proporcionar uno de: drive_id, user_id, group_id, site_id")
                
            if item_id is None and item_path is None:
                raise ValueError("Debe proporcionar item_id o item_path")
            if item_id is not None and item_path is not None:
                raise ValueError("No puede proporcionar item_id e item_path simultáneamente")
                
            if drive_id:
                base_url = f"{self.client.base_url}/drives/{drive_id}"
            elif user_id:
                base_url = f"{self.client.base_url}/users/{user_id}/drive"
            elif group_id:
                base_url = f"{self.client.base_url}/groups/{group_id}/drive"
            elif site_id:
                base_url = f"{self.client.base_url}/sites/{site_id}/drive"
            else:
                base_url = f"{self.client.base_url}/me/drive"
                
            if item_path is not None:
                url = f"{base_url}/root:/{item_path.strip('/')}:/content"
            else:
                url = f"{base_url}/items/{item_id}/content"
                
            headers = {
                'Authorization': f'Bearer {self.client.token}'
            }
            if etag:
                headers['if-none-match'] = etag
            if byte_range:
                headers['Range'] = f'bytes={byte_range[0]}-{byte_range[1]}'
                
            with httpx.Client() as client:
                response = client.get(url, headers=headers, follow_redirects=True)
                
                if response.status_code == 304:
                    logger.info("El archivo no ha sido modificado")
                    return None
                    
                response.raise_for_status()
                
                logger.info(
                    f"Archivo descargado exitosamente "
                    f"({len(response.content)} bytes)"
                )
                return response.content
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error("Error 400: Solicitud incorrecta")
                if "insufficient privileges" in e.response.text.lower():
                    raise PermissionError(
                        "No tiene los permisos necesarios. Se requiere Files.Read o Files.Read.All"
                    ) from e
            elif e.response.status_code == 401:
                logger.error("Error 401: No autorizado")
                raise PermissionError(
                    "Token no válido o expirado. Asegúrese de tener los permisos Files.Read o Files.Read.All"
                ) from e
            elif e.response.status_code == 403:
                logger.error("Error 403: Prohibido")
                raise PermissionError(
                    "No tiene permisos para descargar archivos de este drive. " 
                    "Se requiere Files.Read o Files.Read.All"
                ) from e
            elif e.response.status_code == 404:
                logger.error("Error 404: Archivo no encontrado")
                raise FileNotFoundError("El archivo solicitado no existe") from e
            raise
