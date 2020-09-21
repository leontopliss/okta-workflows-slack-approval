import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

def setup_logger():
    # https://googleapis.dev/python/logging/latest/stdlib-usage.html
    client = google.cloud.logging.Client()
    handler = CloudLoggingHandler(client)
    logger = logging.getLogger('cloudLogger')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger