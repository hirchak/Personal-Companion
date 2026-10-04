"""Durable runtime classifications; content provenance is a separate domain contract."""
from enum import StrEnum

class RootKind(StrEnum):
    SYNTHETIC_TEST = 'SYNTHETIC_TEST'
    PRIVATE_LOCAL = 'PRIVATE_LOCAL'
