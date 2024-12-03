from __future__ import annotations
import bitstring
from bitstring.bitstream import BitStream
from bitstring.utils import tokenparser
from bitstring.exceptions import CreationError
from typing import Union, List
from bitstring.bitstore import BitStore
from bitstring.bitstore_helpers import bitstore_from_token

def pack(fmt: Union[str, List[str]], *values, **kwargs) -> BitStream:
    """Pack the values according to the format string and return a new BitStream.

    fmt -- A single string or a list of strings with comma separated tokens
           describing how to create the BitStream.
    values -- Zero or more values to pack according to the format.
    kwargs -- A dictionary or keyword-value pairs - the keywords used in the
              format string will be replaced with their given value.

    Token examples: 'int:12'    : 12 bits as a signed integer
                    'uint:8'    : 8 bits as an unsigned integer
                    'float:64'  : 8 bytes as a big-endian float
                    'intbe:16'  : 2 bytes as a big-endian signed integer
                    'uintbe:16' : 2 bytes as a big-endian unsigned integer
                    'intle:32'  : 4 bytes as a little-endian signed integer
                    'uintle:32' : 4 bytes as a little-endian unsigned integer
                    'floatle:64': 8 bytes as a little-endian float
                    'intne:24'  : 3 bytes as a native-endian signed integer
                    'uintne:24' : 3 bytes as a native-endian unsigned integer
                    'floatne:32': 4 bytes as a native-endian float
                    'hex:80'    : 80 bits as a hex string
                    'oct:9'     : 9 bits as an octal string
                    'bin:1'     : single bit binary string
                    'ue' / 'uie': next bits as unsigned exp-Golomb code
                    'se' / 'sie': next bits as signed exp-Golomb code
                    'bits:5'    : 5 bits as a bitstring object
                    'bytes:10'  : 10 bytes as a bytes object
                    'bool'      : 1 bit as a bool
                    'pad:3'     : 3 zero bits as padding

    >>> s = pack('uint:12, bits', 100, '0xffe')
    >>> t = pack(['bits', 'bin:3'], s, '111')
    >>> u = pack('uint:8=a, uint:8=b, uint:55=a', a=6, b=44)

    """
    from bitstring.bitstream import BitStream
    from bitstring.utils import tokenparser, expand_brackets

    if isinstance(fmt, list):
        fmt = ','.join(fmt)

    fmt = expand_brackets(fmt)
    _, tokens = tokenparser(fmt, tuple(kwargs.keys()))

    if len(values) + len(kwargs) != len(tokens):
        raise ValueError("Pack string leads to {} arguments, but {} values were provided".format(
            len(tokens), len(values) + len(kwargs)))

    bitstring = BitStream()
    value_index = 0

    for token in tokens:
        name, length, value = token
        if name in kwargs:
            value = kwargs[name]
        elif value is None:
            value = values[value_index]
            value_index += 1
        
        if name == 'bits':
            bitstring.append(BitStream(auto=value, length=length))
        elif name == 'bool':
            bitstring.append(BitStream(bool=value))
        elif name in ('int', 'uint', 'intbe', 'uintbe', 'intle', 'uintle', 'intne', 'uintne'):
            bitstring.append(BitStream(**{name: value, 'length': length}))
        elif name in ('float', 'floatbe', 'floatle', 'floatne'):
            bitstring.append(BitStream(**{name: value}))
        elif name in ('ue', 'se', 'uie', 'sie'):
            bitstring.append(BitStream(**{name: value}))
        elif name in ('hex', 'oct', 'bin'):
            bitstring.append(BitStream(**{name: value, 'length': length}))
        elif name == 'bytes':
            bitstring.append(BitStream(bytes=value, length=length*8))
        elif name == 'pad':
            bitstring.append(BitStream(length=length))
        else:
            raise ValueError(f"Unknown token name: {name}")

    return bitstring
