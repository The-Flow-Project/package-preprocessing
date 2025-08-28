"""
Create preprocessing logger
"""

import os
import logging.config
import yaml

# Ensure log directory exists
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Load logging configuration
current_dir = os.path.dirname(os.path.realpath(__file__))
logging_config = os.path.join(current_dir, "logging_config.yaml")
with open(logging_config, encoding='utf-8') as file:
    config = yaml.safe_load(file)
    logging.config.dictConfig(config)

# Central logger accessible throughout the application
logger = logging.getLogger("preprocessing_logger")
