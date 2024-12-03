from __future__ import annotations
import struct
import math
import functools
from typing import Union, Optional, Dict, Callable
import bitarray
from bitstring.bitstore import BitStore
import bitstring
from bitstring.fp8 import p4binary_fmt, p3binary_fmt
from bitstring.mxfp import e3m2mxfp_fmt, e2m3mxfp_fmt, e2m1mxfp_fmt, e4m3mxfp_saturate_fmt, e5m2mxfp_saturate_fmt, e4m3mxfp_overflow_fmt, e5m2mxfp_overflow_fmt
CACHE_SIZE = 256

def tidy_input_string(s: str) -> str:
    """Return string made lowercase and with all whitespace and underscores removed."""
    return ''.join(c.lower() for c in s if c not in ' \t\n\r\f\v_')
e8m0mxfp_allowed_values = [float(2 ** x) for x in range(-127, 128)]
literal_bit_funcs: Dict[str, Callable[..., BitStore]] = {'0x': hex2bitstore, '0X': hex2bitstore, '0b': bin2bitstore, '0B': bin2bitstore, '0o': oct2bitstore, '0O': oct2bitstore}
