from typing import Optional
import httpx
from ..core.log import Log

logger = Log(__name__)

class AsyncUsers:
    """Clase para manejar operaciones asíncronas relacionadas con usuarios en Microsoft Graph"""
    
    def __init__(self, client):
        self.client = client  # Referencia al cliente principal
        
    async def list_users(
        self, 
        select: Optional[str] = None, 
        filter: Optional[str] = None,
        search: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None
    ) -> dict:
        """
        Lista usuarios de Microsoft Graph con opciones de filtrado y selección.
        
        Args:
            select (str, optional): Propiedades a retornar (ej: "displayName,mail")
            filter (str, optional): Filtro OData (ej: "startsWith(displayName,'A')")
            search (str, optional): Término de búsqueda 
            orderby (str, optional): Campo para ordenar resultados
            top (int, optional): Número máximo de resultados a retornar
            
        Returns:
            dict: Respuesta JSON con la lista de usuarios
            
        Raises:
            Exception: Si hay error en la petición
        """
        if not self.client.token:
            await self.client.get_token()
            
        url = f"{self.client.base_url}/users"
        
        params = {}
        if select:
            params['$select'] = select
        if filter:
            params['$filter'] = filter 
        if search:
            params['$search'] = f'"{search}"'
        if orderby:
            params['$orderby'] = orderby
        if top:
            params['$top'] = str(top)
            
        headers = {
            'Authorization': f'Bearer {self.client.token}',
            'ConsistencyLevel': 'eventual' if search else None
        }
        headers = {k:v for k,v in headers.items() if v is not None}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            logger.info("Usuarios listados exitosamente")
            return response.json()
            
    async def get_user(self, user_id: str, select: Optional[str] = None) -> dict:
        """
        Obtiene información de un usuario específico.
        
        Args:
            user_id (str): ID o userPrincipalName del usuario
            select (str, optional): Propiedades específicas a retornar
            
        Returns:
            dict: Datos del usuario
            
        Raises:
            ValueError: Si user_id está vacío
            Exception: Si hay error en la petición
        """
        if not user_id:
            raise ValueError("user_id es requerido")
            
        if not self.client.token:
            await self.client.get_token()
            
        url = f"{self.client.base_url}/users/{user_id}"
        
        params = {}
        if select:
            params['$select'] = select
            
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Usuario obtenido exitosamente")
            return response.json()

class Users:
    """Clase para manejar operaciones síncronas relacionadas con usuarios en Microsoft Graph"""
    
    def __init__(self, client):
        self.client = client  # Referencia al cliente principal
        
    def list_users(
        self, 
        select: Optional[str] = None, 
        filter: Optional[str] = None,
        search: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None
    ) -> dict:
        """
        Lista usuarios de Microsoft Graph con opciones de filtrado y selección.
        
        Args:
            select (str, optional): Propiedades a retornar (ej: "displayName,mail")
            filter (str, optional): Filtro OData (ej: "startsWith(displayName,'A')")
            search (str, optional): Término de búsqueda 
            orderby (str, optional): Campo para ordenar resultados
            top (int, optional): Número máximo de resultados a retornar
            
        Returns:
            dict: Respuesta JSON con la lista de usuarios
            
        Raises:
            Exception: Si hay error en la petición
        """
        if not self.client.token:
            self.client.get_token()
            
        url = f"{self.client.base_url}/users"
        
        params = {}
        if select:
            params['$select'] = select
        if filter:
            params['$filter'] = filter 
        if search:
            params['$search'] = f'"{search}"'
        if orderby:
            params['$orderby'] = orderby
        if top:
            params['$top'] = str(top)
            
        headers = {
            'Authorization': f'Bearer {self.client.token}',
            'ConsistencyLevel': 'eventual' if search else None
        }
        headers = {k:v for k,v in headers.items() if v is not None}
        
        with httpx.Client() as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            logger.info("Usuarios listados exitosamente")
            return response.json()
            
    def get_user(self, user_id: str, select: Optional[str] = None) -> dict:
        """
        Obtiene información de un usuario específico.
        
        Args:
            user_id (str): ID o userPrincipalName del usuario
            select (str, optional): Propiedades específicas a retornar
            
        Returns:
            dict: Datos del usuario
            
        Raises:
            ValueError: Si user_id está vacío
            Exception: Si hay error en la petición
        """
        if not user_id:
            raise ValueError("user_id es requerido")
            
        if not self.client.token:
            self.client.get_token()
            
        url = f"{self.client.base_url}/users/{user_id}"
        
        params = {}
        if select:
            params['$select'] = select
            
        headers = {
            'Authorization': f'Bearer {self.client.token}'
        }
        
        with httpx.Client() as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Usuario obtenido exitosamente")
            return response.json() 