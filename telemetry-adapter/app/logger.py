import logging
import sys


def configure_logger(is_debug: bool):
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    stream_handler.setFormatter(log_formatter)
    logging.basicConfig(
        level=logging.DEBUG if is_debug else logging.INFO,
        handlers=[stream_handler]
    )
