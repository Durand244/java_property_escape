"""Decode Java ``.properties`` escape sequences.

Java's ``Properties.load`` accepts a small set of backslash escapes inside
values and keys.  This module implements exactly that set:

``\\t``, ``\\n``, ``\\f``, ``\\r``, ``\\\\``, ``\\uXXXX``, and the rule that a
backslash followed by a character that is not one of the above simply drops
the backslash and keeps the character.

A ``\\u`` sequence must be followed by exactly four hexadecimal digits.  Java
itself throws ``IllegalArgumentException`` when it is not; we raise
``ValueError`` instead, because Python callers expect that.

Surrogate pairs are combined: ``\\uD83D\\uDE00`` decodes to a single
astral character, matching what a Java ``String`` would contain.
"""

from __future__ import annotations

__all__ = ["decode", "decode_line"]

_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")

# Java's Properties.load maps these letters to control characters.  The
# mapping is deliberately small: Java does not define \\b, \\a, or \\v.
_SIMPLE_ESCAPES = {
    "t": "\t",
    "n": "\n",
    "f": "\f",
    "r": "\r",
}


def _is_high_surrogate(code: int) -> bool:
    return 0xD800 <= code <= 0xDBFF


def _is_low_surrogate(code: int) -> bool:
    return 0xDC00 <= code <= 0xDFFF


def _combine_surrogates(high: int, low: int) -> str:
    """Combine a UTF-16 surrogate pair into one code point.

    Java strings are UTF-16, so ``\\uD83D\\uDE00`` is a single emoji there.
    Python strings are code-point based, so we must merge the pair ourselves
    to keep decoded output identical to Java's.
    """
    combined = 0x10000 + ((high - 0xD800) << 10) + (low - 0xDC00)
    return chr(combined)


def _decode_hex(text: str, start: int) -> tuple[str, int]:
    """Read four hex digits starting at ``start``; return (char, next_index)."""
    end = start + 4
    if end > len(text):
        raise ValueError(
            "truncated \\u escape at position %d: expected 4 hex digits" % start
        )
    digits = text[start:end]
    for ch in digits:
        if ch not in _HEX_DIGITS:
            raise ValueError(
                "invalid \\u escape at position %d: %r is not a hex digit"
                % (start, ch)
            )
    code = int(digits, 16)
    if _is_high_surrogate(code) and end + 6 <= len(text) and text[end:end + 2] == "\\u":
        low_digits = text[end + 2:end + 6]
        if len(low_digits) == 4 and all(c in _HEX_DIGITS for c in low_digits):
            low = int(low_digits, 16)
            if _is_low_surrogate(low):
                return _combine_surrogates(code, low), end + 6
    return chr(code), end


def decode(text: str) -> str:
    """Decode Java property escape sequences in ``text``.

    Unknown escapes drop the backslash and keep the following character,
    which mirrors ``java.util.Properties.load``.  A trailing lone backslash
    is kept as a literal backslash, again matching Java's behaviour.
    """
    if not isinstance(text, str):
        raise TypeError("decode() expects str, got %r" % type(text).__name__)

    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        if i + 1 >= n:
            # Java keeps a trailing backslash rather than swallowing it.
            out.append("\\")
            break
        nxt = text[i + 1]
        if nxt == "u":
            decoded, i = _decode_hex(text, i + 2)
            out.append(decoded)
        elif nxt in _SIMPLE_ESCAPES:
            out.append(_SIMPLE_ESCAPES[nxt])
            i += 2
        else:
            # Any other escaped character loses its backslash.
            out.append(nxt)
            i += 2
    return "".join(out)


def decode_line(line: str) -> str:
    """Decode one logical properties line.

    This is a thin wrapper around :func:`decode` that also strips a trailing
    newline, since callers reading a file line by line usually want the value
    without the terminator.  It exists so that callers do not have to
    re-implement that small step.
    """
    if not isinstance(line, str):
        raise TypeError("decode_line() expects str, got %r" % type(line).__name__)
    if line.endswith("\r\n"):
        line = line[:-2]
    elif line.endswith("\n") or line.endswith("\r"):
        line = line[:-1]
    return decode(line)
