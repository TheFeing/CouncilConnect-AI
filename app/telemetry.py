# app/telemetry.py
import os                 # For environment variable access
import logging            # For logging telemetry initialisation status
from opentelemetry import metrics                               # Core OpenTelemetry metrics API
from opentelemetry.sdk.metrics import MeterProvider             # SDK implementation of MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader      # For periodic export of metrics
from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter     # Azure Monitor exporter for OpenTelemetry

logger = logging.getLogger(__name__)

# Global meter and counter (will be initialised once)
_meter = None
_pii_redaction_counter = None

def init_telemetry():
    """Initialise OpenTelemetry with Azure Monitor exporter.
       Should be called once at application startup."""
    global _meter, _pii_redaction_counter
    conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not conn_str:
        logger.warning("No Application Insights connection string found. Custom metrics disabled.")
        return

    try:
        exporter = AzureMonitorMetricExporter(connection_string=conn_str)
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)  # every 60s
        provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(provider)
        _meter = metrics.get_meter(__name__)
        _pii_redaction_counter = _meter.create_counter(
            name="pii.redactions.total",
            description="Number of PII redactions performed",
            unit="1"
        )
        logger.info("OpenTelemetry metrics initialised successfully.")
    except Exception as e:
        logger.error(f"Failed to initialise OpenTelemetry: {e}")

def get_pii_redaction_counter():
    """Return the counter object (may be None if telemetry not initialised)."""
    return _pii_redaction_counter