import logging
import os


class Logger:
    def __init__(self, log_file, log_level=logging.DEBUG, console=True, log_format=None):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        formatter = log_format or logging.Formatter(
            '%(asctime)s - %(name)s - %(filename)s - %(levelname)s - %(message)s'
        )

        if console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Extract directory path from the log file
        log_dir = os.path.dirname(log_file)

        # Check if the directory exists, create it if it doesn't
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger
