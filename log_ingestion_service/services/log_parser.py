import re
from datetime import datetime

from models.log_models import NormalizedLogEntry, ParseResult

HTTP_ACCESS_COMMON = "http_access_common"
NGINX_ERROR = "nginx_error"
IIS_HEADER = "iis_header"
IIS_W3C_LINE_FALLBACK = "iis_w3c_line_fallback"
TOMCAT_CATALINA = "tomcat_catalina"
HAPROXY = "haproxy"

SUPPORTED_LOG_TYPES = [
    IIS_HEADER,
    NGINX_ERROR,
    HAPROXY,
    TOMCAT_CATALINA,
    HTTP_ACCESS_COMMON,
    IIS_W3C_LINE_FALLBACK,
]

# Required detection regexes from modifications.md
HTTP_ACCESS_COMMON_RE = re.compile(
    r'^\S+ \S+ \S+ \[[0-9]{2}/[A-Za-z]{3}/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2} [+\-][0-9]{4}\] "[A-Z]+ [^"]+ HTTP/[0-9.]+" [0-9]{3} (\d+|-) "[^"]*" "[^"]*"$'
)

NGINX_ERROR_RE = re.compile(
    r"^[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} \[(debug|info|notice|warn|error|crit|alert|emerg)\] \d+#\d+: (\*\d+ )?.*$"
)

IIS_FIELDS_HEADER_RE = re.compile(
    r"^#Fields:\s+.+$"
)

IIS_W3C_LINE_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} \S+ \S+ \S+ \S+ \S+ \S+ \S+ .*$"
)

TOMCAT_CATALINA_RE = re.compile(
    r"^[0-9]{2}-[A-Za-z]{3}-[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} (INFO|WARN|ERROR|DEBUG|TRACE|FATAL) \[[^\]]+\] .+$"
)

HAPROXY_RE = re.compile(
    r"^[A-Za-z]{3} [ 0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} \S+ haproxy\[\d+\]: \S+:\d+ \[[0-9]{2}/[A-Za-z]{3}/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2}\.\d+\] .+$"
)

HTTP_ACCESS_COMMON_EXTRACT_RE = re.compile(
    r'^(?P<client_ip>\S+) \S+ \S+ \[(?P<timestamp>[0-9]{2}/[A-Za-z]{3}/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2} [+\-][0-9]{4})\] "(?P<request>[A-Z]+ [^"]+ HTTP/[0-9.]+)" (?P<status>[0-9]{3}) (?P<body_bytes>\d+|-) "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"$'
)

NGINX_ERROR_EXTRACT_RE = re.compile(
    r"^(?P<timestamp>[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}) \[(?P<severity>debug|info|notice|warn|error|crit|alert|emerg)\] (?P<worker>\d+#\d+): (?P<message>.*)$"
)

TOMCAT_CATALINA_EXTRACT_RE = re.compile(
    r"^(?P<timestamp>[0-9]{2}-[A-Za-z]{3}-[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}) (?P<severity>INFO|WARN|ERROR|DEBUG|TRACE|FATAL) \[(?P<thread>[^\]]+)\] (?P<message>.+)$"
)

HAPROXY_EXTRACT_RE = re.compile(
    r"^(?P<syslog_month>[A-Za-z]{3}) (?P<syslog_day>[ 0-9]{2}) (?P<syslog_time>[0-9]{2}:[0-9]{2}:[0-9]{2}) (?P<host>\S+) haproxy\[(?P<pid>\d+)\]: (?P<client_ip>\S+):(?P<client_port>\d+) \[(?P<accept_date>[0-9]{2}/[A-Za-z]{3}/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+)\] (?P<message>.+)$"
)


class LogFormatError(ValueError):
    pass


def _status_to_severity(status: str | None) -> str | None:
    if status is None:
        return None
    try:
        code = int(status)
    except ValueError:
        return None

    if code >= 500:
        return "error"
    if code >= 400:
        return "warn"
    return "info"


def _to_iso(value: str, format_string: str) -> str:
    return datetime.strptime(value, format_string).isoformat()


def _all_match(lines: list[str], pattern: re.Pattern[str]) -> bool:
    return all(pattern.fullmatch(line) is not None for line in lines)


def _parse_http_access_common_line(line: str) -> NormalizedLogEntry:
    match = HTTP_ACCESS_COMMON_EXTRACT_RE.fullmatch(line)
    if match is None:
        raise LogFormatError("Failed to parse HTTP access common line.")

    status = match.group("status")
    return NormalizedLogEntry(
        log_type=HTTP_ACCESS_COMMON,
        raw_line=line,
        message=match.group("request"),
        timestamp=_to_iso(match.group("timestamp"), "%d/%b/%Y:%H:%M:%S %z"),
        severity=_status_to_severity(status),
        parsed_fields={
            "client_ip": match.group("client_ip"),
            "request": match.group("request"),
            "status": status,
            "body_bytes": match.group("body_bytes"),
            "referrer": match.group("referrer"),
            "user_agent": match.group("user_agent"),
        },
    )


def _parse_nginx_error_line(line: str) -> NormalizedLogEntry:
    match = NGINX_ERROR_EXTRACT_RE.fullmatch(line)
    if match is None:
        raise LogFormatError("Failed to parse Nginx error line.")

    return NormalizedLogEntry(
        log_type=NGINX_ERROR,
        raw_line=line,
        message=match.group("message"),
        timestamp=_to_iso(match.group("timestamp"), "%Y/%m/%d %H:%M:%S"),
        severity=match.group("severity"),
        parsed_fields={
            "worker": match.group("worker"),
        },
    )


def _parse_tomcat_catalina_line(line: str) -> NormalizedLogEntry:
    match = TOMCAT_CATALINA_EXTRACT_RE.fullmatch(line)
    if match is None:
        raise LogFormatError("Failed to parse Tomcat catalina line.")

    return NormalizedLogEntry(
        log_type=TOMCAT_CATALINA,
        raw_line=line,
        message=match.group("message"),
        timestamp=_to_iso(match.group("timestamp"), "%d-%b-%Y %H:%M:%S.%f"),
        severity=match.group("severity").lower(),
        parsed_fields={
            "thread": match.group("thread"),
        },
    )


def _parse_haproxy_line(line: str) -> NormalizedLogEntry:
    match = HAPROXY_EXTRACT_RE.fullmatch(line)
    if match is None:
        raise LogFormatError("Failed to parse HAProxy line.")

    return NormalizedLogEntry(
        log_type=HAPROXY,
        raw_line=line,
        message=match.group("message"),
        timestamp=_to_iso(match.group("accept_date"), "%d/%b/%Y:%H:%M:%S.%f"),
        severity=None,
        parsed_fields={
            "host": match.group("host"),
            "pid": match.group("pid"),
            "client_ip": match.group("client_ip"),
            "client_port": match.group("client_port"),
        },
    )


def _parse_iis_fields_header_line(line: str) -> NormalizedLogEntry:
    fields_part = line.split(":", maxsplit=1)[1].strip()
    return NormalizedLogEntry(
        log_type=IIS_HEADER,
        raw_line=line,
        message=f"IIS fields header: {fields_part}",
        timestamp=None,
        severity=None,
        parsed_fields={
            "fields": fields_part,
        },
    )


def _parse_iis_w3c_line(line: str) -> NormalizedLogEntry:
    parts = line.split()
    if len(parts) < 10:
        raise LogFormatError("Failed to parse IIS W3C line.")

    date_part = parts[0]
    time_part = parts[1]
    timestamp = _to_iso(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")

    parsed_fields = {
        "server_ip": parts[2] if len(parts) > 2 else "",
        "method": parts[3] if len(parts) > 3 else "",
        "uri_stem": parts[4] if len(parts) > 4 else "",
        "uri_query": parts[5] if len(parts) > 5 else "",
        "server_port": parts[6] if len(parts) > 6 else "",
        "username": parts[7] if len(parts) > 7 else "",
        "client_ip": parts[8] if len(parts) > 8 else "",
        "user_agent": parts[9] if len(parts) > 9 else "",
        "status": parts[10] if len(parts) > 10 else "",
        "substatus": parts[11] if len(parts) > 11 else "",
        "win32_status": parts[12] if len(parts) > 12 else "",
        "time_taken": parts[13] if len(parts) > 13 else "",
    }

    method = parsed_fields["method"] or "UNKNOWN"
    uri_stem = parsed_fields["uri_stem"] or "-"

    return NormalizedLogEntry(
        log_type=IIS_W3C_LINE_FALLBACK,
        raw_line=line,
        message=f"{method} {uri_stem}",
        timestamp=timestamp,
        severity=_status_to_severity(parsed_fields.get("status") or None),
        parsed_fields=parsed_fields,
    )


def detect_and_normalize_log(content: str) -> ParseResult:
    if not content or not content.strip():
        raise LogFormatError("Uploaded .log file is empty.")

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        raise LogFormatError("Uploaded .log file is empty.")

    if IIS_FIELDS_HEADER_RE.fullmatch(lines[0]) and len(lines) > 1 and _all_match(
        lines[1:], IIS_W3C_LINE_RE
    ):
        entries = [_parse_iis_fields_header_line(lines[0])]
        entries.extend(_parse_iis_w3c_line(line) for line in lines[1:])
        return ParseResult(detected_log_type=IIS_HEADER, entries=entries)

    if _all_match(lines, IIS_FIELDS_HEADER_RE):
        return ParseResult(
            detected_log_type=IIS_HEADER,
            entries=[_parse_iis_fields_header_line(line) for line in lines],
        )

    if _all_match(lines, NGINX_ERROR_RE):
        return ParseResult(
            detected_log_type=NGINX_ERROR,
            entries=[_parse_nginx_error_line(line) for line in lines],
        )

    if _all_match(lines, HAPROXY_RE):
        return ParseResult(
            detected_log_type=HAPROXY,
            entries=[_parse_haproxy_line(line) for line in lines],
        )

    if _all_match(lines, TOMCAT_CATALINA_RE):
        return ParseResult(
            detected_log_type=TOMCAT_CATALINA,
            entries=[_parse_tomcat_catalina_line(line) for line in lines],
        )

    if _all_match(lines, HTTP_ACCESS_COMMON_RE):
        return ParseResult(
            detected_log_type=HTTP_ACCESS_COMMON,
            entries=[_parse_http_access_common_line(line) for line in lines],
        )

    if _all_match(lines, IIS_W3C_LINE_RE):
        return ParseResult(
            detected_log_type=IIS_W3C_LINE_FALLBACK,
            entries=[_parse_iis_w3c_line(line) for line in lines],
        )

    raise LogFormatError(
        "Unsupported log format. Supported types are: "
        + ", ".join(SUPPORTED_LOG_TYPES)
    )
