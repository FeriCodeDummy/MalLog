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


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except ValueError:
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
            },
        }

    error_count = 0
    warn_count = 0
    suspicious_messages = 0

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
            if status_code >= 500:
                entry_error = True
            elif status_code >= 400 and not entry_error:
                entry_warn = True

        if entry_error:
            error_count += 1
        elif entry_warn:
            warn_count += 1

        searchable = f"{message} {raw_line} {log_type}".lower()
        if any(keyword in searchable for keyword in SUSPICIOUS_KEYWORDS):
            suspicious_messages += 1

    error_ratio = error_count / total
    warn_ratio = warn_count / total
    suspicious_ratio = suspicious_messages / total

    score = 0.0
    reasons: list[str] = []

    if error_ratio >= 0.30:
        score += 0.5
        reasons.append(
            f"High ERROR-like ratio detected ({error_count}/{total}, {error_ratio:.2%})."
        )
    if warn_ratio >= 0.50:
        score += 0.3
        reasons.append(
            f"High WARN-like ratio detected ({warn_count}/{total}, {warn_ratio:.2%})."
        )
    if suspicious_ratio >= 0.20:
        score += 0.4
        reasons.append(
            "High number of suspicious keywords in messages "
            f"({suspicious_messages}/{total}, {suspicious_ratio:.2%})."
        )

    score = min(score, 1.0)
    label = "ANOMALY" if score >= 0.6 else "NORMAL"

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
        },
    }
