import unittest

from services.log_parser import LogFormatError, detect_and_normalize_log


class TestLogParser(unittest.TestCase):
    def test_detects_nginx_error(self):
        content = (
            '2026/03/30 14:22:05 [error] 1234#1234: *12 open() "/var/www/favicon.ico" '
            'failed (2: No such file or directory), client: 127.0.0.1, server: localhost, '
            'request: "GET /favicon.ico HTTP/1.1", host: "localhost"'
        )
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_log_type, "nginx_error")
        self.assertEqual(result.entries[0].severity, "error")

    def test_detects_iis_w3c_line_fallback(self):
        content = (
            "2026-03-30 14:22:01 10.0.0.5 GET /index.html - 80 - "
            "192.168.1.10 Mozilla/5.0 200 0 0 123"
        )
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_log_type, "iis_w3c_line_fallback")
        self.assertEqual(result.entries[0].parsed_fields["method"], "GET")

    def test_detects_iis_header_with_fallback_lines(self):
        content = "\n".join(
            [
                "#Fields: date time s-ip cs-method cs-uri-stem cs-uri-query s-port cs-username c-ip cs(User-Agent) sc-status sc-substatus sc-win32-status time-taken",
                "2026-03-30 14:22:01 10.0.0.5 GET /index.html - 80 - 192.168.1.10 Mozilla/5.0 200 0 0 123",
            ]
        )
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_log_type, "iis_header")
        self.assertEqual(result.entries[0].log_type, "iis_header")
        self.assertEqual(result.entries[1].log_type, "iis_w3c_line_fallback")

    def test_detects_tomcat_catalina(self):
        content = (
            "30-Mar-2026 14:24:55.123 ERROR [http-nio-8080-exec-10] "
            "org.apache.catalina.core.StandardWrapperValve.invoke Servlet.service() for servlet "
            "[dispatcher] threw exception java.lang.NullPointerException"
        )
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_log_type, "tomcat_catalina")
        self.assertEqual(result.entries[0].severity, "error")

    def test_detects_haproxy(self):
        content = (
            'Mar 30 14:22:01 localhost haproxy[1234]: 192.168.1.10:54321 '
            '[30/Mar/2026:14:22:01.123] frontend backend/server1 0/0/1/2/3 200 512 - - ---- '
            '1/1/0/0/0 0/0 "GET / HTTP/1.1"'
        )
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_log_type, "haproxy")
        self.assertEqual(result.entries[0].parsed_fields["client_ip"], "192.168.1.10")

    def test_detects_http_access_common(self):
        content = (
            '127.0.0.1 - - [30/Mar/2026:14:22:01 +0200] "GET /index.html HTTP/1.1" '
            '200 612 "-" "Mozilla/5.0"'
        )
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_log_type, "http_access_common")
        self.assertEqual(result.entries[0].parsed_fields["status"], "200")

    def test_unsupported_format_fails(self):
        content = "[INFO] [07/02/2024 09:42:48] old-style log format"
        with self.assertRaises(LogFormatError):
            detect_and_normalize_log(content)

    def test_empty_payload_fails(self):
        with self.assertRaises(LogFormatError):
            detect_and_normalize_log(" ")


if __name__ == "__main__":
    unittest.main()
