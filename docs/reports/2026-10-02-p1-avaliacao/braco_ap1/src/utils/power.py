from __future__ import annotations

import ctypes
import logging
import sys
from contextlib import contextmanager
from typing import Iterator


logger = logging.getLogger(__name__)

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


@contextmanager
def prevent_system_sleep(enabled: bool = True, reason: str = "build") -> Iterator[None]:
    """Prevent Windows from suspending the system while a long task is running."""
    if not enabled or sys.platform != "win32":
        yield
        return

    kernel32 = getattr(getattr(ctypes, "windll", None), "kernel32", None)
    if kernel32 is None:
        yield
        return

    try:
        result = kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        if result:
            logger.info("[power] Prevenindo suspensao do sistema durante %s.", reason)
        else:
            logger.warning("[power] Falha ao ativar prevencao de suspensao para %s.", reason)
        yield
    finally:
        try:
            result = kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            if result:
                logger.info("[power] Prevencao de suspensao liberada apos %s.", reason)
            else:
                logger.warning("[power] Falha ao liberar prevencao de suspensao apos %s.", reason)
        except Exception as e:
            logger.warning("[power] Falha ao restaurar estado de energia apos %s: %s", reason, e)
