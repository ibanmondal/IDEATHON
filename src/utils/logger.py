import logging
import os
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

def setup_logger(name: str = "nutrisense") -> logging.Logger:
    """
    Setup Google Cloud Logging if GCP_PROJECT_ID is present,
    otherwise fallback to standard console logging.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Remove existing handlers to prevent duplicates
    if logger.handlers:
        logger.handlers.clear()

    project_id = os.environ.get("GCP_PROJECT_ID")
    
    if project_id:
        try:
            client = google.cloud.logging.Client(project=project_id)
            handler = CloudLoggingHandler(client)
            logger.addHandler(handler)
        except Exception as e:
            # Fallback if there's an authentication or connection issue
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            logger.warning(f"Failed to initialize Google Cloud Logging, using console: {str(e)}")
    else:
        # Standard logging fallback
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

logger = setup_logger()
