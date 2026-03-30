from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NormalizedLogEntry:
    log_type: str
    raw_line: str
    message: str
    timestamp: str | None
    severity: str | None
    parsed_fields: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "log_type": self.log_type,
            "raw_line": self.raw_line,
            "message": self.message,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "parsed_fields": self.parsed_fields,
        }


@dataclass(frozen=True)
class ParseResult:
    detected_log_type: str
    entries: list[NormalizedLogEntry]

    def to_payload(self) -> dict[str, Any]:
        return {
            "log_type": self.detected_log_type,
            "entry_count": len(self.entries),
            "entries": [entry.to_dict() for entry in self.entries],
        }
