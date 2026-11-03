import unittest

from java_property_escape import decode, decode_line
from java_property_escape.core import decode as core_decode


class TestDecode(unittest.TestCase):
    def test_plain_text_is_unchanged(self):
        self.assertEqual(decode("hello world"), "hello world")

    def test_empty_string(self):
        self.assertEqual(decode(""), "")

    def test_simple_escapes(self):
        self.assertEqual(decode(r"a\tb"), "a\tb")
        self.assertEqual(decode(r"a\nb"), "a\nb")
        self.assertEqual(decode(r"a\fb"), "a\fb")
        self.assertEqual(decode(r"a\rb"), "a\rb")

    def test_escaped_backslash(self):
        self.assertEqual(decode(r"a\\b"), "a\\b")

    def test_unknown_escape_drops_backslash(self):
        # Java's Properties.load keeps the character but drops the backslash.
        self.assertEqual(decode(r"a\qb"), "aqb")
        self.assertEqual(decode(r"\:"), ":")

    def test_unicode_escape(self):
        self.assertEqual(decode(r"\u0041"), "A")
        self.assertEqual(decode(r"a\u00e9b"), "a\u00e9b")

    def test_uppercase_hex_digits(self):
        self.assertEqual(decode(r"\u00E9"), "\u00e9")

    def test_surrogate_pair_is_combined(self):
        # U+1F600 GRINNING FACE as a UTF-16 surrogate pair.
        self.assertEqual(decode(r"\uD83D\uDE00"), "\U0001F600")

    def test_lone_high_surrogate_is_not_combined(self):
        # No low surrogate follows, so the high surrogate stands alone.
        self.assertEqual(decode(r"\uD83Dx"), "\ud83dx")

    def test_invalid_hex_raises(self):
        with self.assertRaises(ValueError):
            decode(r"\uZZZZ")

    def test_truncated_escape_raises(self):
        with self.assertRaises(ValueError):
            decode(r"\u12")

    def test_trailing_backslash_is_kept(self):
        self.assertEqual(decode("abc\\"), "abc\\")

    def test_type_error_on_non_string(self):
        with self.assertRaises(TypeError):
            decode(b"bytes")

    def test_core_reexport_matches(self):
        self.assertIs(decode, core_decode)


class TestDecodeLine(unittest.TestCase):
    def test_strips_lf(self):
        self.assertEqual(decode_line("a\\nb\n"), "a\nb")

    def test_strips_crlf(self):
        self.assertEqual(decode_line("a\\nb\r\n"), "a\nb")

    def test_strips_cr(self):
        self.assertEqual(decode_line("a\\nb\r"), "a\nb")

    def test_no_terminator(self):
        self.assertEqual(decode_line("a\\nb"), "a\nb")

    def test_type_error_on_non_string(self):
        with self.assertRaises(TypeError):
            decode_line(3)


if __name__ == "__main__":
    unittest.main()
