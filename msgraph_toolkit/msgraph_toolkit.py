import json
import httpx
from dotenv import load_dotenv

from msgraph_toolkit.core.log import Log
from msgraph_toolkit.base import MsGraphBase

load_dotenv(override=True)

logger = Log(__name__)

class MsGraph(MsGraphBase):
    """Implementación síncrona del cliente Microsoft Graph"""
    
    def get_token(self) -> str:
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
        
        with httpx.Client() as client:
            response = client.post(self.token_url, data=data)
            response.raise_for_status()
            token_response = response.json()
            
            if 'access_token' not in token_response:
                logger.error("No se recibió access_token en la respuesta")
                logger.error(f"Respuesta completa: {json.dumps(token_response, indent=2)}")
                raise Exception("No se pudo obtener el token de acceso")
                
            self.token = token_response.get('access_token')
            logger.info("Token obtenido exitosamente")
            return self.token

