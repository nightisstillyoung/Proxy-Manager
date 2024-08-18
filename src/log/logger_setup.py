import logging

from configs.config import DEV

log_level = logging.INFO if DEV else logging.ERROR

# prints information in console
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# writes logs in file
file_handler = logging.FileHandler('log/last.log')
file_handler.setLevel(log_level)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

if DEV:
    file_handler.mode = "w"
else:
    file_handler.mode = "a"

# config for basicConfig()
log_conf = {
    "level": log_level,
}

