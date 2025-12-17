"""
Create preprocessing logger
"""

import os
import logging.config

# Ensure log directory exists
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(filename)s - %(levelname)s - %(message)s',
        },
        'brief': {
            'format': '%(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'logs/preprocessing.log',
            'mode': 'a',
            'encoding': 'utf-8',
            'maxBytes': 5242880,  # 5 MB
            'backupCount': 5,
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'brief',
        },
    },
    'loggers': {
        'preprocessing_logger': {
            'level': 'INFO',
            'handlers': ['file', 'console'],
            'propagate': False,
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['file', 'console'],
    },
}

# Load logging configuration
logging.config.dictConfig(logging_config)

# Central logger accessible throughout the application
logger = logging.getLogger("preprocessing_logger")
