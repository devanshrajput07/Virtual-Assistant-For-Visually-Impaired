import logging
import logging.handlers
import os

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "aura.log")

def setup_logging(level: str = "INFO") -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    if root.handlers:
        return logging.getLogger("aura")

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    return logging.getLogger("aura")

logger = logging.getLogger("aura")
