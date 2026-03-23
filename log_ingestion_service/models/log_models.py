from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedLogEntry:
    timestamp: str
    message: str
    type: str

    def to_dict(self) -> dict[str, str]:
        return {
            "timestamp": self.timestamp,
            "message": self.message,
            "type": self.type,
        }


@dataclass(frozen=True)
class ParseResult:
    detected_format: str
    entries: list[NormalizedLogEntry]

    def to_payload(self) -> dict[str, list[dict[str, str]]]:
        return {"entries": [entry.to_dict() for entry in self.entries]}
