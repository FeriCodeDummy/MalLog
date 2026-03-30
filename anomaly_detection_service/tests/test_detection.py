import unittest

from app.detection import run_anomaly_detection


class TestDetectionLogic(unittest.TestCase):
    def test_marks_anomaly_when_error_signal_is_high(self):
        entries = [
            {
                "log_type": "nginx_error",
                "raw_line": "x",
                "message": "failed login",
                "severity": "error",
                "timestamp": "2026-03-01T10:00:00",
                "parsed_fields": {},
            },
            {
                "log_type": "tomcat_catalina",
                "raw_line": "x",
                "message": "nullpointer exception",
                "severity": "fatal",
                "timestamp": "2026-03-01T10:00:01",
                "parsed_fields": {},
            },
            {
                "log_type": "http_access_common",
                "raw_line": "x",
                "message": "GET /",
                "severity": "info",
                "timestamp": "2026-03-01T10:00:02",
                "parsed_fields": {"status": "200"},
            },
        ]

        result = run_anomaly_detection(entries)
        self.assertEqual(result["label"], "ANOMALY")
        self.assertGreaterEqual(result["score"], 0.6)

    def test_marks_normal_when_signal_is_low(self):
        entries = [
            {
                "log_type": "http_access_common",
                "raw_line": "x",
                "message": "GET /home",
                "severity": "info",
                "timestamp": "2026-03-01T10:00:00",
                "parsed_fields": {"status": "200"},
            },
            {
                "log_type": "iis_w3c_line_fallback",
                "raw_line": "x",
                "message": "GET /docs",
                "severity": "info",
                "timestamp": "2026-03-01T10:00:01",
                "parsed_fields": {"status": "200"},
            },
            {
                "log_type": "haproxy",
                "raw_line": "x",
                "message": "GET /ok",
                "severity": None,
                "timestamp": "2026-03-01T10:00:02",
                "parsed_fields": {},
            },
        ]

        result = run_anomaly_detection(entries)
        self.assertEqual(result["label"], "NORMAL")
        self.assertLess(result["score"], 0.6)


if __name__ == "__main__":
    unittest.main()
