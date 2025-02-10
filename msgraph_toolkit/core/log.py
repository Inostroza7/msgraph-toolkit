import logging
import os
from logging.handlers import TimedRotatingFileHandler

from dotenv import load_dotenv

load_dotenv(override=True)

class Log:
    """Clase para configurar el sistema de logging."""

    def __init__(self, name=__name__, log_level=None, log_to_file=False, log_filename='application.log'):
        """Inicializa el logger.
        
        Args:
            name (str): Nombre del logger.
            log_level (str, opcional): Nivel de logging ('DEBUG', 'INFO', 'WARNING', etc.).
            log_to_file (bool, opcional): Si debe escribir en un archivo (por defecto, desactivado).
            log_filename (str, opcional): Nombre del archivo de log (si log_to_file es True).
        """
        self.logger = logging.getLogger(name)
        self.logger.handlers = []  # Limpiar handlers anteriores

        # Evitar la propagación de logs al logger raíz
        self.logger.propagate = False
        
        # Cargar nivel de logging desde argumento o variable de entorno
        log_level = log_level or os.getenv('LOG_LEVEL', 'WARNING').upper()
        self.logger.setLevel(log_level)
        
        # Configurar formateador
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Configurar logging en consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Configurar logging en archivo si se requiere
        if log_to_file:
            file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1)
            file_handler.suffix = "%Y%m%d"
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Configurar el nivel de logging específico para `httpx`
        httpx_logger = logging.getLogger('httpx')
        httpx_logger.handlers = [] 
        httpx_logger.setLevel(logging.WARNING)
        httpx_logger.addHandler(console_handler)
        if log_to_file:
            httpx_logger.addHandler(file_handler)

    def __getattr__(self, name):
        """Permite que las llamadas al logger se realicen directamente desde la instancia de Log."""
        return getattr(self.logger, name)

# Configurar el logger raíz para manejar logs no capturados
root_logger = logging.getLogger()
root_logger.handlers = []  # Limpiar handlers existentes
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

logger = Log()