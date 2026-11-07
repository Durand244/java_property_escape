# java_property_escape

Decode Java `.properties` escape sequences (`\t`, `\n`, `\f`, `\r`, `\\`,
`\uXXXX`, and unknown `\x`) into ordinary Python strings.

```python
from java_property_escape import decode, decode_line

decode(r"caf\u00e9")
# 'café'

decode(r"line1\nline2")
# 'line1\nline2'

decode_line("key=value\n")
# 'key=value'
```

## Why this exists

Java's `Properties.load` treats backslashes in property values as escapes.
When you read a `.properties` file in Python and want the same string Java
would produce, `str.encode`/`unicode_escape` is not a substitute: it decodes
`\b`, `\a`, `\v`, `\xHH`, and octal escapes that Java does not, and it leaves
UTF-16 surrogate pairs split apart. This library implements the Java rule set
and nothing else.

The trade-off: we raise `ValueError` on a malformed `\u` escape instead of
silently dropping it. Java throws `IllegalArgumentException` in that case, so
the exception is faithful; a lenient decoder would be easier to feed garbage
to, but it would hide corrupt property files.

## The awkward edge

A `\u` escape must have exactly four hex digits, and a high surrogate is only
merged with a following low surrogate. A lone `\uD83D` stays as a lone
surrogate code point in the returned string, which Python will happily hold
but will refuse to encode as UTF-8. That matches what Java's `String`
contains, but if you plan to write the result to a UTF-8 file, validate it
first.

## API

- `decode(text: str) -> str` — decode all escapes in `text`.
- `decode_line(line: str) -> str` — strip one trailing line terminator
  (`\n`, `\r`, or `\r\n`) and then call `decode`.

Both raise `TypeError` if given a non-string. `decode` raises `ValueError`
for a truncated or non-hex `\u` escape.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

