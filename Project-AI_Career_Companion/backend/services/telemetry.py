import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
import os
from .mlflow_service import get_secret

INSTRUMENTATION_KEY = get_secret("AppInsightsKey")

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=f'InstrumentationKey={INSTRUMENTATION_KEY}'))

def log_event(message: str):
    logger.warning(message)
