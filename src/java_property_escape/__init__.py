"""Public API for java_property_escape.

Only the documented names are re-exported here so that callers can rely on
``java_property_escape.decode`` and ``java_property_escape.decode_line``
without reaching into the ``core`` submodule.
"""

from .core import decode, decode_line

__all__ = ["decode", "decode_line"]
