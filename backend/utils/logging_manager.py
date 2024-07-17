# logging_manager.py

import os
import logging
from datetime import datetime

class LoggingManager:
    def __init__(self, log_directory='./logs'):
        self.log_directory = log_directory
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

    def _get_log_filename(self, log_type):
        return f"{self.log_directory}/{log_type}_{datetime.now().strftime('%Y-%m-%d')}.log"

    def configure_logging(self, log_type):
        log_filename = self._get_log_filename(log_type)
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format="%(asctime)s %(levelname)s:%(message)s",
        )
        logging.getLogger().addHandler(logging.StreamHandler())  # Optional: To also log to console
        logging.info(f"{log_type.capitalize()} logging configured successfully.")

    def get_logger(self, log_type):
        log_filename = self._get_log_filename(log_type)
        logger = logging.getLogger(log_type)
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(log_filename)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s %(levelname)s:%(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(logging.StreamHandler())  # Optional: To also log to console
        return logger
