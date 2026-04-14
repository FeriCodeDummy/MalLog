import unittest

from app.detection import run_anomaly_detection


class TestDetectionLogic(unittest.TestCase):
    def _http_entry(self, *, ip: str, path: str, status: str, severity: str = "info"):
        request = f"GET {path} HTTP/1.1"
        return {
            "log_type": "http_access_common",
            "raw_line": f'{ip} - - [30/Mar/2026:14:00:00 +0200] "{request}" {status} 512 "-" "Mozilla/5.0"',
            "message": request,
            "severity": severity,
            "timestamp": "2026-03-30T12:00:00",
            "parsed_fields": {
                "client_ip": ip,
                "request": request,
                "status": status,
            },
        }

    def test_http_profiles_match_generator_modes(self):
        normal_entries = [
            self._http_entry(ip="10.0.0.1", path="/", status="200"),
            self._http_entry(ip="10.0.0.2", path="/index.html", status="200"),
            self._http_entry(ip="10.0.0.3", path="/api/data", status="404", severity="warn"),
            self._http_entry(ip="10.0.0.4", path="/", status="200"),
            self._http_entry(ip="10.0.0.5", path="/api/data", status="500", severity="error"),
            self._http_entry(ip="10.0.0.6", path="/index.html", status="200"),
        ]
        warning_entries = [
            self._http_entry(ip="10.0.1.1", path="/login", status="200"),
            self._http_entry(ip="10.0.1.2", path="/admin", status="401", severity="warn"),
            self._http_entry(ip="10.0.1.3", path="/api/login", status="403", severity="warn"),
            self._http_entry(ip="10.0.1.4", path="/login", status="500", severity="error"),
            self._http_entry(ip="10.0.1.5", path="/admin", status="200"),
            self._http_entry(ip="10.0.1.6", path="/api/login", status="401", severity="warn"),
        ]
        anomaly_entries = [
            self._http_entry(
                ip="192.168.1.100",
                path="/admin",
                status="401",
                severity="warn",
            ),
            self._http_entry(
                ip="192.168.1.100",
                path="/admin/login",
                status="403",
                severity="warn",
            ),
            self._http_entry(
                ip="192.168.1.100",
                path="/wp-admin",
                status="500",
                severity="error",
            ),
            self._http_entry(
                ip="192.168.1.100",
                path="/config",
                status="500",
                severity="error",
            ),
            self._http_entry(
                ip="192.168.1.100",
                path="/admin",
                status="403",
                severity="warn",
            ),
            self._http_entry(
                ip="192.168.1.100",
                path="/admin/login",
                status="401",
                severity="warn",
            ),
        ]

        normal_result = run_anomaly_detection(normal_entries)
        warning_result = run_anomaly_detection(warning_entries)
        anomaly_result = run_anomaly_detection(anomaly_entries)

        self.assertEqual(normal_result["label"], "NORMAL")
        self.assertEqual(warning_result["label"], "WARNING")
        self.assertEqual(anomaly_result["label"], "ANOMALY")

    def test_marks_anomaly_for_fixed_attacker_ip_in_nginx_style_logs(self):
        entries = [
            {
                "log_type": "nginx_error",
                "raw_line": '2026/03/30 14:10:00 [warn] 1234#4567: *11 failure, client: 192.168.1.100, request: "GET /admin HTTP/1.1"',
                "message": "failure, client: 192.168.1.100",
                "severity": "warn",
                "timestamp": "2026-03-30T12:10:00",
                "parsed_fields": {},
            },
            {
                "log_type": "nginx_error",
                "raw_line": '2026/03/30 14:10:01 [error] 1234#4567: *12 failure, client: 192.168.1.100, request: "POST /admin HTTP/1.1"',
                "message": "failure, client: 192.168.1.100",
                "severity": "error",
                "timestamp": "2026-03-30T12:10:01",
                "parsed_fields": {},
            },
            {
                "log_type": "nginx_error",
                "raw_line": '2026/03/30 14:10:02 [crit] 1234#4567: *13 failure, client: 192.168.1.100, request: "GET /admin HTTP/1.1"',
                "message": "failure, client: 192.168.1.100",
                "severity": "crit",
                "timestamp": "2026-03-30T12:10:02",
                "parsed_fields": {},
            },
        ]

        result = run_anomaly_detection(entries)
        self.assertEqual(result["label"], "ANOMALY")
        self.assertGreaterEqual(result["score"], 0.7)


if __name__ == "__main__":
    unittest.main()
