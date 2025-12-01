import logging
from logging.handlers import RotatingFileHandler

# Create logger
logger = logging.getLogger("chatbot_logger")
logger.setLevel(logging.INFO)

# Log format
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler (5 MB per file, max 3 backups)
file_handler = RotatingFileHandler(
    "chatbot.log", 
    maxBytes=5*1024*1024,
    backupCount=3
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

