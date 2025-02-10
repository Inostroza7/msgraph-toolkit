import os
from dotenv import load_dotenv
from msgraph_toolkit.core.log import Log

load_dotenv(override=True)
logger = Log(__name__)

class MsGraphBase:
    """
    Clase base con la configuración común para las versiones sync y async de Microsoft Graph API.
    
    Esta clase maneja la configuración básica necesaria para autenticarse y comunicarse con 
    Microsoft Graph API, incluyendo las credenciales del cliente y URLs base.
    """
    
    def __init__(
            self,
            client_id: str = os.getenv('CLIENT_ID'),
            client_secret: str = os.getenv('CLIENT_SECRET'),
            tenant_id: str = os.getenv('TENANT_ID'),
            ):
        """
        Inicializa la configuración base para el cliente de Microsoft Graph.
        
        Args:
            client_id (str): ID del cliente de Azure AD. Se puede obtener del portal de Azure.
            client_secret (str): Secreto del cliente de Azure AD.
            tenant_id (str): ID del inquilino de Azure AD que identifica la organización.
            
        Raises:
            ValueError: Si falta alguna de las credenciales requeridas.
        """
        # Validar credenciales
        if not client_id:
            logger.error("No se ha proporcionado CLIENT_ID")
            raise ValueError("CLIENT_ID es requerido. Configúrelo en las variables de entorno o páselo como parámetro.")
            
        if not client_secret:
            logger.error("No se ha proporcionado CLIENT_SECRET")
            raise ValueError("CLIENT_SECRET es requerido. Configúrelo en las variables de entorno o páselo como parámetro.")
            
        if not tenant_id:
            logger.error("No se ha proporcionado TENANT_ID")
            raise ValueError("TENANT_ID es requerido. Configúrelo en las variables de entorno o páselo como parámetro.")
        
        logger.debug(f"Inicializando MsGraphBase con client_id: {client_id[:5]}... y tenant_id: {tenant_id}")
        
        self.token = None
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        
        # URLs base para la API
        self.base_url = 'https://graph.microsoft.com/v1.0'
        self.token_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        
        self.is_delegated = False  # Por defecto usa client credentials
        
        logger.info("MsGraphBase inicializado correctamente")