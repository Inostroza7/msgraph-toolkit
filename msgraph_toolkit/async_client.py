import httpx
import json

from msgraph_toolkit.base import MsGraphBase
from msgraph_toolkit.core.log import Log
from .toolkit.users import AsyncUsers
from .toolkit.drives import AsyncDrives
from .toolkit.mails import AsyncMails
logger = Log(__name__)

class AsyncMsGraph(MsGraphBase):
    """Implementación asíncrona del cliente Microsoft Graph"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.users = AsyncUsers(self)
        self.drives = AsyncDrives(self)
        self.mails = AsyncMails(self)

# ------------------------------------------------------------------------------------------------
# Token
# ------------------------------------------------------------------------------------------------
    async def get_token(self) -> str:
        """
        Obtiene el token de acceso usando client credentials flow
        Los permisos deben estar configurados y consentidos en Azure Portal
        
        Returns:
            str: Token de acceso
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            token_response = response.json()
            
            if 'access_token' not in token_response:
                logger.error("No se recibió access_token en la respuesta")
                logger.error(f"Respuesta completa: {json.dumps(token_response, indent=2)}")
                raise Exception("No se pudo obtener el token de acceso")
                
            self.token = token_response.get('access_token')
            logger.info("Token obtenido exitosamente")
            return self.token
