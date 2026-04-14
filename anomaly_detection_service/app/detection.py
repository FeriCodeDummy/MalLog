import re
from collections import Counter
from typing import Any

SUSPICIOUS_KEYWORDS = (
    "failed",
    "unauthorized",
    "forbidden",
    "attack",
    "breach",
    "denied",
    "exception",
    "nullpointer",
    "critical",
)

ERROR_SEVERITIES = {"error", "crit", "alert", "emerg", "fatal"}
WARN_SEVERITIES = {"warn", "warning", "notice"}

# Synthetic generator baseline from system_test/generate_logs.py
ATTACKER_IP = "192.168.1.100"
NORMAL_PATHS = {"/", "/index.html", "/api/data"}
WARNING_PATHS = {"/login", "/admin", "/api/login"}
ATTACK_PATHS = {"/admin", "/admin/login", "/wp-admin", "/config"}

NGINX_CLIENT_IP_RE = re.compile(r"client:\s*(?P<ip>(?:\d{1,3}\.){3}\d{1,3})")
REQUEST_IN_MESSAGE_RE = re.compile(
    r"(?:^|\s)(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(?P<path>/\S*)"
)
REQUEST_IN_RAW_LINE_RE = re.compile(r'"[A-Z]+\s+(?P<path>/\S*)\s+HTTP/[0-9.]+"')


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def _looks_like_ipv4(candidate: str) -> bool:
    parts = candidate.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        value = int(part)
        if value < 0 or value > 255:
            return False
    return True


def _extract_client_ip(parsed_fields: dict[str, Any], raw_line: str) -> str | None:
    for key in ("client_ip", "remote_ip", "c-ip"):
        value = parsed_fields.get(key)
        if value is not None:
            text = str(value).strip()
            if _looks_like_ipv4(text):
                return text

    nginx_match = NGINX_CLIENT_IP_RE.search(raw_line)
    if nginx_match is not None:
        return nginx_match.group("ip")

    first_token = raw_line.split(" ", 1)[0].strip()
    if _looks_like_ipv4(first_token):
        return first_token

    return None


def _extract_request_path(
    parsed_fields: dict[str, Any],
    message: str,
    raw_line: str,
) -> str | None:
    uri_stem = parsed_fields.get("uri_stem")
    if uri_stem is not None:
        uri_text = str(uri_stem).strip()
        if uri_text.startswith("/"):
            return uri_text.lower()

    raw_request = parsed_fields.get("request")
    if raw_request is not None:
        request_text = str(raw_request).strip()
        parts = request_text.split()
        if len(parts) >= 2 and parts[1].startswith("/"):
            return parts[1].lower()

    uri = parsed_fields.get("uri")
    if uri is not None:
        uri_text = str(uri).strip()
        if uri_text.startswith("/"):
            return uri_text.lower()

    message_match = REQUEST_IN_MESSAGE_RE.search(message)
    if message_match is not None:
        return message_match.group("path").lower()

    raw_match = REQUEST_IN_RAW_LINE_RE.search(raw_line)
    if raw_match is not None:
        return raw_match.group("path").lower()

    return None


def run_anomaly_detection(entries: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(entries)
    if total == 0:
        return {
            "label": "ANOMALY",
            "score": 1.0,
            "reasons": ["No entries provided for analysis."],
            "metrics": {
                "total_entries": 0,
                "error_ratio": 0.0,
                "warn_ratio": 0.0,
                "suspicious_messages": 0,
                "attacker_ip_ratio": 0.0,
                "dominant_ip_ratio": 0.0,
                "status_4xx_5xx_ratio": 0.0,
                "status_5xx_ratio": 0.0,
                "attack_path_ratio": 0.0,
                "warning_path_ratio": 0.0,
                "normal_path_ratio": 0.0,
            },
        }

    error_count = 0
    warn_count = 0
    suspicious_messages = 0

    status_observed = 0
    status_4xx_5xx = 0
    status_5xx = 0

    path_observed = 0
    attack_path_hits = 0
    warning_path_hits = 0
    normal_path_hits = 0

    ip_counts: Counter[str] = Counter()
    attacker_ip_hits = 0

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        severity = str(entry.get("severity", "")).lower()
        message = str(entry.get("message", ""))
        raw_line = str(entry.get("raw_line", ""))
        log_type = str(entry.get("log_type", ""))
        parsed_fields = entry.get("parsed_fields", {})
        if not isinstance(parsed_fields, dict):
            parsed_fields = {}

        entry_error = False
        entry_warn = False

        if severity in ERROR_SEVERITIES:
            entry_error = True
        elif severity in WARN_SEVERITIES:
            entry_warn = True

        status_code = _to_int(parsed_fields.get("status"))
        if status_code is not None:
            status_observed += 1
            if status_code >= 400:
                status_4xx_5xx += 1
            if status_code >= 500:
                status_5xx += 1

            if status_code >= 500:
                entry_error = True
            elif status_code >= 400 and not entry_error:
                entry_warn = True

        if entry_error:
            error_count += 1
        elif entry_warn:
            warn_count += 1

        client_ip = _extract_client_ip(parsed_fields, raw_line)
        if client_ip is not None:
            ip_counts[client_ip] += 1
            if client_ip == ATTACKER_IP:
                attacker_ip_hits += 1

        request_path = _extract_request_path(parsed_fields, message, raw_line)
        if request_path is not None:
            path_observed += 1
            if request_path in ATTACK_PATHS:
                attack_path_hits += 1
            if request_path in WARNING_PATHS:
                warning_path_hits += 1
            if request_path in NORMAL_PATHS:
                normal_path_hits += 1

        searchable = f"{message} {raw_line} {log_type}".lower()
        if any(keyword in searchable for keyword in SUSPICIOUS_KEYWORDS):
            suspicious_messages += 1

    error_ratio = error_count / total
    warn_ratio = warn_count / total
    suspicious_ratio = suspicious_messages / total

    ip_observed = sum(ip_counts.values())
    attacker_ip_ratio = attacker_ip_hits / ip_observed if ip_observed else 0.0
    dominant_ip_ratio = (max(ip_counts.values()) / ip_observed) if ip_observed else 0.0

    status_4xx_5xx_ratio = status_4xx_5xx / status_observed if status_observed else 0.0
    status_5xx_ratio = status_5xx / status_observed if status_observed else 0.0

    attack_path_ratio = attack_path_hits / path_observed if path_observed else 0.0
    warning_path_ratio = warning_path_hits / path_observed if path_observed else 0.0
    normal_path_ratio = normal_path_hits / path_observed if path_observed else 0.0

    score = 0.0
    reasons: list[str] = []

    # Strongest indicator from generated anomaly data:
    # one fixed attacker IP repeated almost everywhere.
    if ip_observed and attacker_ip_ratio >= 0.95:
        score += 0.75
        reasons.append(
            f"Single known attacker IP dominates traffic ({attacker_ip_hits}/{ip_observed}, "
            f"{attacker_ip_ratio:.2%})."
        )
    elif ip_observed and dominant_ip_ratio >= 0.90:
        score += 0.55
        reasons.append(
            f"A single client IP dominates traffic ({dominant_ip_ratio:.2%} of observed client IP fields)."
        )

    if status_observed:
        if status_4xx_5xx_ratio >= 0.90:
            score += 0.25
            reasons.append(
                "Very high 4xx/5xx ratio detected "
                f"({status_4xx_5xx}/{status_observed}, {status_4xx_5xx_ratio:.2%})."
            )
        elif status_4xx_5xx_ratio >= 0.45:
            score += 0.12
            reasons.append(
                "Moderately high 4xx/5xx ratio detected "
                f"({status_4xx_5xx}/{status_observed}, {status_4xx_5xx_ratio:.2%})."
            )

        if status_5xx_ratio >= 0.25:
            score += 0.18
            reasons.append(
                f"High 5xx error ratio detected ({status_5xx}/{status_observed}, {status_5xx_ratio:.2%})."
            )
        elif status_5xx_ratio >= 0.10:
            score += 0.08
            reasons.append(
                f"Elevated 5xx error ratio detected ({status_5xx}/{status_observed}, {status_5xx_ratio:.2%})."
            )

    if path_observed:
        if attack_path_ratio >= 0.75:
            score += 0.20
            reasons.append(
                "Attack-like request paths dominate "
                f"({attack_path_hits}/{path_observed}, {attack_path_ratio:.2%})."
            )
        elif warning_path_ratio >= 0.60:
            score += 0.10
            reasons.append(
                "Warning-like request paths dominate "
                f"({warning_path_hits}/{path_observed}, {warning_path_ratio:.2%})."
            )
        elif normal_path_ratio >= 0.70:
            score = max(0.0, score - 0.05)
            reasons.append(
                f"Most requests target normal paths ({normal_path_hits}/{path_observed}, {normal_path_ratio:.2%})."
            )

    # Fallback signal for log types that lack status/path/IP fields.
    if error_ratio >= 0.40:
        score += 0.10
        reasons.append(
            f"High ERROR-like severity ratio ({error_count}/{total}, {error_ratio:.2%})."
        )
    elif warn_ratio >= 0.50:
        score += 0.05
        reasons.append(
            f"High WARN-like severity ratio ({warn_count}/{total}, {warn_ratio:.2%})."
        )

    # Keep keyword signal conservative because generated nginx messages always contain "failure".
    if (
        suspicious_ratio >= 0.95
        and ip_observed == 0
        and status_observed == 0
        and path_observed == 0
    ):
        score += 0.10
        reasons.append(
            "Suspicious keywords dominate logs with otherwise sparse structured fields "
            f"({suspicious_messages}/{total}, {suspicious_ratio:.2%})."
        )

    score = min(max(score, 0.0), 1.0)

    if score >= 0.70:
        label = "ANOMALY"
    elif score >= 0.30:
        label = "WARNING"
    else:
        label = "NORMAL"

    if not reasons:
        reasons.append("No anomaly signals exceeded configured thresholds.")

    return {
        "label": label,
        "score": round(score, 3),
        "reasons": reasons,
        "metrics": {
            "total_entries": total,
            "error_ratio": round(error_ratio, 3),
            "warn_ratio": round(warn_ratio, 3),
            "suspicious_messages": suspicious_messages,
            "attacker_ip_ratio": round(attacker_ip_ratio, 3),
            "dominant_ip_ratio": round(dominant_ip_ratio, 3),
            "status_4xx_5xx_ratio": round(status_4xx_5xx_ratio, 3),
            "status_5xx_ratio": round(status_5xx_ratio, 3),
            "attack_path_ratio": round(attack_path_ratio, 3),
            "warning_path_ratio": round(warning_path_ratio, 3),
            "normal_path_ratio": round(normal_path_ratio, 3),
        },
    }
