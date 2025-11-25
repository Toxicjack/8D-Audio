"""Project version and runtime compatibility helpers."""

from __future__ import annotations

import logging
import sys
from typing import Tuple

VERSION: str = "4.6.0-alpha"
MIN_PYTHON_VERSION: Tuple[int, int] = (3, 14)


def require_runtime_python(logger: logging.Logger | None = None) -> None:
    """Log whether the current interpreter meets the targeted Python version.

    The project now targets Python 3.14 for its alpha feature set. To keep the
    application usable on environments that have not yet upgraded, we emit a
    warning rather than raising an exception when the runtime is older. Once
    Python 3.14 is available in production, this helper can be tightened to
    enforce the minimum version.
    """

    logger = logger or logging.getLogger(__name__)
    current = sys.version_info
    target = f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}"
    running = f"{current.major}.{current.minor}.{current.micro}"

    if (current.major, current.minor) < MIN_PYTHON_VERSION:
        logger.warning(
            "Python %s detected; this alpha targets %s or newer. Behaviour is best-effort on older interpreters.",
            running,
            target,
        )
    else:
        logger.info("Detected Python %s which meets the target runtime %s+", running, target)

