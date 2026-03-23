import re
from datetime import datetime

from models.log_models import NormalizedLogEntry, ParseResult

TIMESTAMP_INPUT_FORMAT = "%m/%d/%Y %H:%M:%S"

SUPPORTED_FORMATS = [
    "[TYPE] TIMESTAMP message",
    "TIMESTAMP [TYPE] message",
    "[TYPE] (TIMESTAMP) message",
    "<TIMESTAMP> (TYPE) message",
    "TIMESTAMP (TYPE) message",
    "TYPE <TIMESTAMP> message",
]

_TIMESTAMP_VALUE = r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}"
_BRACKETED_TIMESTAMP = rf"\[(?P<timestamp>{_TIMESTAMP_VALUE})\]"
_TYPE = r"(?P<type>INFO|ERROR|WARN)"
_MESSAGE = r"(?P<message>[^;\r\n]+)"

_FORMAT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        SUPPORTED_FORMATS[0],
        re.compile(rf"^\[{_TYPE}\] {_BRACKETED_TIMESTAMP} {_MESSAGE}$"),
    ),
    (
        SUPPORTED_FORMATS[1],
        re.compile(rf"^{_BRACKETED_TIMESTAMP} \[{_TYPE}\] {_MESSAGE}$"),
    ),
    (
        SUPPORTED_FORMATS[2],
        re.compile(rf"^\[{_TYPE}\] \({_BRACKETED_TIMESTAMP}\) {_MESSAGE}$"),
    ),
    (
        SUPPORTED_FORMATS[3],
        re.compile(rf"^<{_BRACKETED_TIMESTAMP}> \({_TYPE}\) {_MESSAGE}$"),
    ),
    (
        SUPPORTED_FORMATS[4],
        re.compile(rf"^{_BRACKETED_TIMESTAMP} \({_TYPE}\) {_MESSAGE}$"),
    ),
    (
        SUPPORTED_FORMATS[5],
        re.compile(rf"^{_TYPE} <{_BRACKETED_TIMESTAMP}> {_MESSAGE}$"),
    ),
]


class LogFormatError(ValueError):
    pass


def _normalize_timestamp(value: str) -> str:
    timestamp = datetime.strptime(value, TIMESTAMP_INPUT_FORMAT)
    return timestamp.isoformat()


def _parse_with_pattern(
    lines: list[str], format_name: str, pattern: re.Pattern[str]
) -> ParseResult | None:
    entries: list[NormalizedLogEntry] = []

    for line in lines:
        match = pattern.fullmatch(line)
        if match is None:
            return None

        message = match.group("message")
        if not message or ";" in message:
            return None

        timestamp_value = match.group("timestamp")
        try:
            normalized_timestamp = _normalize_timestamp(timestamp_value)
        except ValueError:
            return None

        entries.append(
            NormalizedLogEntry(
                timestamp=normalized_timestamp,
                message=message,
                type=match.group("type"),
            )
        )

    if not entries:
        raise LogFormatError("Uploaded .log file is empty.")

    return ParseResult(detected_format=format_name, entries=entries)


def detect_and_normalize_log(content: str) -> ParseResult:
    if not content or not content.strip():
        raise LogFormatError("Uploaded .log file is empty.")

    lines = content.splitlines()
    if not lines:
        raise LogFormatError("Uploaded .log file is empty.")

    if any(not line.strip() for line in lines):
        raise LogFormatError("Log file contains empty lines, which are not supported.")

    for format_name, pattern in _FORMAT_PATTERNS:
        parsed = _parse_with_pattern(lines, format_name, pattern)
        if parsed is not None:
            return parsed

    raise LogFormatError(
        "Unsupported log format. Supported forms are: "
        + ", ".join(SUPPORTED_FORMATS)
    )
