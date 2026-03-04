import logging
import os
from logging.handlers import RotatingFileHandler
from config import AUDIT_LOG_FILE
from app.core.security.security_service import SecurityService

_LOGGER = None


def _get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger("bloyckter.audit")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
        handler = RotatingFileHandler(
            AUDIT_LOG_FILE,
            maxBytes=1_048_576,
            backupCount=3,
            encoding="utf-8",
        )
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if os.path.exists(AUDIT_LOG_FILE):
            SecurityService.restrict_permission(AUDIT_LOG_FILE)

    _LOGGER = logger
    return logger


class AuditService:
    @staticmethod
    def record(event: str, details: str):
        _get_logger().info("%s | %s", event, details)

    @staticmethod
    def record_error(event: str, details: str):
        _get_logger().error("%s | %s", event, details)
