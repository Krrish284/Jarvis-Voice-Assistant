from __future__ import annotations

import logging
import sys

from .config import Settings
from .core.engine import AssistantEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    config = Settings()

    if config.text_mode:
        logger.info("Starting in text mode (no microphone required)")
    else:
        logger.info("Starting voice assistant (push-to-talk mode)")
        logger.info("Press Ctrl+C to exit")

    engine = AssistantEngine(config)

    try:
        engine.run()
    except KeyboardInterrupt:
        logger.info("Received exit signal")
    except Exception:
        logger.exception("Fatal error")
        sys.exit(1)
    finally:
        engine.cleanup()


if __name__ == "__main__":
    main()
