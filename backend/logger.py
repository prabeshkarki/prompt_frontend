# import logging
# from logging.handlers import RotatingFileHandler

# # Single shared logger for the app
# logger = logging.getLogger("chatbot")

# if not logger.handlers:  # avoid duplicate handlers on reload
#     logger.setLevel(logging.INFO)

#     formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

#     # Log to console
#     console_handler = logging.StreamHandler()
#     console_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)

#     # Log to rotating file (5 MB x 3 backups)
#     file_handler = RotatingFileHandler(
#         "chatbot.log",
#         maxBytes=5 * 1024 * 1024,
#         backupCount=3,
#         encoding="utf-8",
#     )
#     file_handler.setFormatter(formatter)
#     logger.addHandler(file_handler)