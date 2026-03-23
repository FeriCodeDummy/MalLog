import unittest

from services.log_parser import LogFormatError, detect_and_normalize_log


class TestLogParser(unittest.TestCase):
    def test_format_1(self):
        content = "[INFO] [07/02/2024 09:42:48] service started"
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_format, "[TYPE] TIMESTAMP message")
        self.assertEqual(result.entries[0].type, "INFO")
        self.assertEqual(result.entries[0].timestamp, "2024-07-02T09:42:48")

    def test_format_2(self):
        content = "[07/02/2024 09:42:48] [ERROR] failed auth"
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_format, "TIMESTAMP [TYPE] message")
        self.assertEqual(result.entries[0].type, "ERROR")

    def test_format_3(self):
        content = "[WARN] ([07/02/2024 09:42:48]) delayed response"
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_format, "[TYPE] (TIMESTAMP) message")
        self.assertEqual(result.entries[0].type, "WARN")

    def test_format_4(self):
        content = "<[07/02/2024 09:42:48]> (INFO) token refreshed"
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_format, "<TIMESTAMP> (TYPE) message")
        self.assertEqual(result.entries[0].type, "INFO")

    def test_format_5(self):
        content = "[07/02/2024 09:42:48] (ERROR) connection dropped"
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_format, "TIMESTAMP (TYPE) message")
        self.assertEqual(result.entries[0].type, "ERROR")

    def test_format_6(self):
        content = "WARN <[07/02/2024 09:42:48]> high cpu usage"
        result = detect_and_normalize_log(content)
        self.assertEqual(result.detected_format, "TYPE <TIMESTAMP> message")
        self.assertEqual(result.entries[0].type, "WARN")

    def test_mixed_formats_fail(self):
        content = "\n".join(
            [
                "[INFO] [07/02/2024 09:42:48] first line",
                "[07/02/2024 09:42:49] [INFO] second line",
            ]
        )
        with self.assertRaises(LogFormatError):
            detect_and_normalize_log(content)

    def test_semicolon_in_message_fails(self):
        content = "[INFO] [07/02/2024 09:42:48] has;semicolon"
        with self.assertRaises(LogFormatError):
            detect_and_normalize_log(content)

    def test_empty_payload_fails(self):
        with self.assertRaises(LogFormatError):
            detect_and_normalize_log(" ")


if __name__ == "__main__":
    unittest.main()
