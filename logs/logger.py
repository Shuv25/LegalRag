"""
Configuring the get_logger function which can be used in any function to log on terminal
"""

import os
import logging
import inspect
from dotenv import load_dotenv

load_dotenv()

APPLICATION_NAME = os.getenv("APPLICATION_NAME")

logging.basicConfig(
    level=logging.INFO,
    format=f'%(asctime)s – {APPLICATION_NAME} - %(name)s – %(levelname)s – %(message)s',
)

def get_logger() -> logging.Logger:
    """
    Returns a configured logger.
    Output format:
    timestamp | application_name | module.path | level | message
    """
    frame = inspect.stack()[1]
    file_path = str(os.path.splitext(os.path.relpath(frame[1]))[0])
    name = file_path.replace(os.sep,'.')
    logger = logging.getLogger(name)

    return logger