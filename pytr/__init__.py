"""pytr - Python SDK and CLI for the Trade Republic broker API."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from pytr.api import TradeRepublicApi, TradeRepublicError
from pytr.event import ConditionalEventType, Event, EventType, PPEventType
from pytr.sdk import LoginError, login
from pytr.timeline import Timeline
from pytr.transactions import TransactionExporter

try:
    __version__ = _pkg_version("pytr")
except PackageNotFoundError:  # local dev install without metadata
    __version__ = "unknown"

__all__ = [
    "ConditionalEventType",
    "Event",
    "EventType",
    "LoginError",
    "PPEventType",
    "Timeline",
    "TradeRepublicApi",
    "TradeRepublicError",
    "TransactionExporter",
    "__version__",
    "login",
]
