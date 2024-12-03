from __future__ import annotations
import bitstring
from bitstring.bits import Bits, BitsType
from bitstring.dtypes import Dtype
from typing import Union, List, Any, Optional, overload, TypeVar, Tuple
import copy
import numbers
TConstBitStream = TypeVar('TConstBitStream', bound='ConstBitStream')

class ConstBitStream(Bits):
    """A container or stream holding an immutable sequence of bits.

    For a mutable container use the BitStream class instead.

    Methods inherited from Bits:

    all() -- Check if all specified bits are set to 1 or 0.
    any() -- Check if any of specified bits are set to 1 or 0.
    copy() -- Return a copy of the bitstring.
    count() -- Count the number of bits set to 1 or 0.
    cut() -- Create generator of constant sized chunks.
    endswith() -- Return whether the bitstring ends with a sub-string.
    find() -- Find a sub-bitstring in the current bitstring.
    findall() -- Find all occurrences of a sub-bitstring in the current bitstring.
    fromstring() -- Create a bitstring from a formatted string.
    join() -- Join bitstrings together using current bitstring.
    pp() -- Pretty print the bitstring.
    rfind() -- Seek backwards to find a sub-bitstring.
    split() -- Create generator of chunks split by a delimiter.
    startswith() -- Return whether the bitstring starts with a sub-bitstring.
    tobitarray() -- Return bitstring as a bitarray from the bitarray package.
    tobytes() -- Return bitstring as bytes, padding if needed.
    tofile() -- Write bitstring to file, padding if needed.
    unpack() -- Interpret bits using format string.

    Other methods:

    bytealign() -- Align to next byte boundary.
    peek() -- Peek at and interpret next bits as a single item.
    peeklist() -- Peek at and interpret next bits as a list of items.
    read() -- Read and interpret next bits as a single item.
    readlist() -- Read and interpret next bits as a list of items.
    readto() -- Read up to and including next occurrence of a bitstring.

    Special methods:

    Also available are the operators [], ==, !=, +, *, ~, <<, >>, &, |, ^.

    Properties:

    [GENERATED_PROPERTY_DESCRIPTIONS]

    len -- Length of the bitstring in bits.
    pos -- The current bit position in the bitstring.
    """
    __slots__ = ('_pos',)

    def __init__(self, auto: Optional[Union[BitsType, int]]=None, /, length: Optional[int]=None, offset: Optional[int]=None, pos: int=0, **kwargs) -> None:
        """Either specify an 'auto' initialiser:
        A string of comma separated tokens, an integer, a file object,
        a bytearray, a boolean iterable or another bitstring.

        Or initialise via **kwargs with one (and only one) of:
        bin -- binary string representation, e.g. '0b001010'.
        hex -- hexadecimal string representation, e.g. '0x2ef'
        oct -- octal string representation, e.g. '0o777'.
        bytes -- raw data as a bytes object, for example read from a binary file.
        int -- a signed integer.
        uint -- an unsigned integer.
        float / floatbe -- a big-endian floating point number.
        bool -- a boolean (True or False).
        se -- a signed exponential-Golomb code.
        ue -- an unsigned exponential-Golomb code.
        sie -- a signed interleaved exponential-Golomb code.
        uie -- an unsigned interleaved exponential-Golomb code.
        floatle -- a little-endian floating point number.
        floatne -- a native-endian floating point number.
        bfloat / bfloatbe - a big-endian bfloat format 16-bit floating point number.
        bfloatle -- a little-endian bfloat format 16-bit floating point number.
        bfloatne -- a native-endian bfloat format 16-bit floating point number.
        intbe -- a signed big-endian whole byte integer.
        intle -- a signed little-endian whole byte integer.
        intne -- a signed native-endian whole byte integer.
        uintbe -- an unsigned big-endian whole byte integer.
        uintle -- an unsigned little-endian whole byte integer.
        uintne -- an unsigned native-endian whole byte integer.
        filename -- the path of a file which will be opened in binary read-only mode.

        Other keyword arguments:
        length -- length of the bitstring in bits, if needed and appropriate.
                  It must be supplied for all integer and float initialisers.
        offset -- bit offset to the data. These offset bits are
                  ignored and this is mainly intended for use when
                  initialising using 'bytes' or 'filename'.
        pos -- Initial bit position, defaults to 0.

        """
        if pos < 0:
            pos += len(self._bitstore)
        if pos < 0 or pos > len(self._bitstore):
            raise bitstring.CreationError(f'Cannot set pos to {pos} when length is {len(self._bitstore)}.')
        self._pos = pos
        self._bitstore.immutable = True

    def _setbytepos(self, bytepos: int) -> None:
        """Move to absolute byte-aligned position in stream."""
        if bytepos * 8 > len(self):
            raise ValueError("Byte position beyond end of bitstring")
        self._pos = bytepos * 8

    def _getbytepos(self) -> int:
        """Return the current position in the stream in bytes. Must be byte aligned."""
        if self._pos % 8:
            raise ValueError("Current position is not byte aligned")
        return self._pos // 8

    def _setbitpos(self, pos: int) -> None:
        """Move to absolute position bit in bitstream."""
        if pos < 0 or pos > len(self):
            raise ValueError("Bit position out of range")
        self._pos = pos

    def _getbitpos(self) -> int:
        """Return the current position in the stream in bits."""
        return self._pos

    def __copy__(self: TConstBitStream) -> TConstBitStream:
        """Return a new copy of the ConstBitStream for the copy module."""
        s = self.__class__()
        s._bitstore = self._bitstore
        s._pos = 0
        return s

    def __and__(self: TConstBitStream, bs: BitsType, /) -> TConstBitStream:
        """Bit-wise 'and' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '&' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        s = Bits.__and__(self, bs)
        s._pos = 0
        return s

    def __or__(self: TConstBitStream, bs: BitsType, /) -> TConstBitStream:
        """Bit-wise 'or' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '|' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        s = Bits.__or__(self, bs)
        s._pos = 0
        return s

    def __xor__(self: TConstBitStream, bs: BitsType, /) -> TConstBitStream:
        """Bit-wise 'xor' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '^' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        s = Bits.__xor__(self, bs)
        s._pos = 0
        return s

    def __add__(self: TConstBitStream, bs: BitsType, /) -> TConstBitStream:
        """Concatenate bitstrings and return new bitstring.

        bs -- the bitstring to append.

        """
        s = Bits.__add__(self, bs)
        s._pos = 0
        return s

    def append(self, bs: BitsType, /) -> None:
        """Append a bitstring to the current bitstring.

        bs -- The bitstring to append.

        The current bit position will be moved to the end of the BitStream.

        """
        bs = self.__class__._create_from_bitstype(bs)
        self._addright(bs)
        self._pos = len(self)

    def __repr__(self) -> str:
        """Return representation that could be used to recreate the bitstring.

        If the returned string is too long it will be truncated. See __str__().

        """
        return self._repr(self.__class__.__name__, len(self), self._pos)

    def overwrite(self, bs: BitsType, /, pos: Optional[int]=None) -> None:
        """Overwrite with bitstring at bit position pos.

        bs -- The bitstring to overwrite with.
        pos -- The bit position to begin overwriting from.

        The current bit position will be moved to the end of the overwritten section.
        Raises ValueError if pos < 0 or pos > len(self).

        """
        bs = self.__class__._create_from_bitstype(bs)
        if pos is None:
            pos = self._pos
        if pos < 0 or pos > len(self):
            raise ValueError("Overwrite position out of range")
        
        end = pos + len(bs)
        if end > len(self):
            self._addright(BitStore(end - len(self)))
        
        self._overwrite(bs, pos)
        self._pos = end

    def find(self, bs: BitsType, /, start: Optional[int]=None, end: Optional[int]=None, bytealigned: Optional[bool]=None) -> Union[Tuple[int], Tuple[()]]:
        """Find first occurrence of substring bs.

        Returns a single item tuple with the bit position if found, or an
        empty tuple if not found. The bit position (pos property) will
        also be set to the start of the substring if it is found.

        bs -- The bitstring to find.
        start -- The bit position to start the search. Defaults to 0.
        end -- The bit position one past the last bit to search.
               Defaults to len(self).
        bytealigned -- If True the bitstring will only be
                       found on byte boundaries.

        Raises ValueError if bs is empty, if start < 0, if end > len(self) or
        if end < start.

        >>> BitStream('0xc3e').find('0b1111')
        (6,)

        """
        pass

    def rfind(self, bs: BitsType, /, start: Optional[int]=None, end: Optional[int]=None, bytealigned: Optional[bool]=None) -> Union[Tuple[int], Tuple[()]]:
        """Find final occurrence of substring bs.

        Returns a single item tuple with the bit position if found, or an
        empty tuple if not found. The bit position (pos property) will
        also be set to the start of the substring if it is found.

        bs -- The bitstring to find.
        start -- The bit position to end the reverse search. Defaults to 0.
        end -- The bit position one past the first bit to reverse search.
               Defaults to len(self).
        bytealigned -- If True the bitstring will only be found on byte
                       boundaries.

        Raises ValueError if bs is empty, if start < 0, if end > len(self) or
        if end < start.

        """
        bs = self.__class__._create_from_bitstype(bs)
        if not bs:
            raise ValueError("Cannot find an empty bitstring")
        
        start, end = self._validate_slice(start, end)
        if bytealigned is None:
            bytealigned = bitstring.bitstring_options.bytealigned
        
        p = self._rfind_msb0(bs, start, end, bytealigned)
        if p:
            self._pos = p[0]
        return p

    def read(self, fmt: Union[int, str, Dtype]) -> Union[int, float, str, Bits, bool, bytes, None]:
        """Interpret next bits according to the format string and return result.

        fmt -- Token string describing how to interpret the next bits.

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
                        'ue'        : next bits as unsigned exp-Golomb code
                        'se'        : next bits as signed exp-Golomb code
                        'uie'       : next bits as unsigned interleaved exp-Golomb code
                        'sie'       : next bits as signed interleaved exp-Golomb code
                        'bits:5'    : 5 bits as a bitstring
                        'bytes:10'  : 10 bytes as a bytes object
                        'bool'      : 1 bit as a bool
                        'pad:3'     : 3 bits of padding to ignore - returns None

        fmt may also be an integer, which will be treated like the 'bits' token.

        The position in the bitstring is advanced to after the read items.

        Raises ReadError if not enough bits are available.
        Raises ValueError if the format is not understood.

        """
        if isinstance(fmt, numbers.Integral):
            fmt = f'bits:{fmt}'
        
        if isinstance(fmt, str):
            name, length = utils.parse_fmt(fmt)
        elif isinstance(fmt, Dtype):
            name, length = fmt.name, fmt.length
        else:
            raise ValueError("Format must be a string, integer, or Dtype")
        
        if self._pos + length > len(self):
            raise bitstring.ReadError(f"Not enough bits available to read {fmt}")
        
        value, new_pos = self._readtoken(name, self._pos, length)
        self._pos = new_pos
        return value

    def readlist(self, fmt: Union[str, List[Union[int, str, Dtype]]], **kwargs) -> List[Union[int, float, str, Bits, bool, bytes, None]]:
        """Interpret next bits according to format string(s) and return list.

        fmt -- A single string or list of strings with comma separated tokens
               describing how to interpret the next bits in the bitstring. Items
               can also be integers, for reading new bitstring of the given length.
        kwargs -- A dictionary or keyword-value pairs - the keywords used in the
                  format string will be replaced with their given value.

        The position in the bitstring is advanced to after the read items.

        Raises ReadError is not enough bits are available.
        Raises ValueError if the format is not understood.

        See the docstring for 'read' for token examples. 'pad' tokens are skipped
        and not added to the returned list.

        >>> h, b1, b2 = s.readlist('hex:20, bin:5, bin:3')
        >>> i, bs1, bs2 = s.readlist(['uint:12', 10, 10])

        """
        if isinstance(fmt, str):
            fmt = [f.strip() for f in fmt.split(',')]
        
        return_values = []
        for f in fmt:
            if isinstance(f, numbers.Integral):
                f = f'bits:{f}'
            if isinstance(f, str):
                name, length = utils.parse_fmt(f)
                if name in kwargs:
                    length = kwargs[name]
            elif isinstance(f, Dtype):
                name, length = f.name, f.length
            else:
                raise ValueError("Format must be a string, integer, or Dtype")
            
            if self._pos + length > len(self):
                raise bitstring.ReadError(f"Not enough bits available to read {f}")
            
            value, new_pos = self._readtoken(name, self._pos, length)
            self._pos = new_pos
            if name != 'pad':
                return_values.append(value)
        
        return return_values

    def readto(self: TConstBitStream, bs: BitsType, /, bytealigned: Optional[bool]=None) -> TConstBitStream:
        """Read up to and including next occurrence of bs and return result.

        bs -- The bitstring to find.
        bytealigned -- If True the bitstring will only be
                       found on byte boundaries.

        Raises ValueError if bs is empty.
        Raises ReadError if bs is not found.

        """
        bs = self.__class__._create_from_bitstype(bs)
        if not bs:
            raise ValueError("Cannot read to an empty bitstring")
        
        found = self.find(bs, start=self._pos, bytealigned=bytealigned)
        if not found:
            raise bitstring.ReadError(f"Substring {bs} not found")
        
        result = self._slice(self._pos, found[0] + len(bs))
        self._pos = found[0] + len(bs)
        return result

    def peek(self: TConstBitStream, fmt: Union[int, str]) -> Union[int, float, str, TConstBitStream, bool, bytes, None]:
        """Interpret next bits according to format string and return result.

        fmt -- Token string describing how to interpret the next bits.

        The position in the bitstring is not changed. If not enough bits are
        available then all bits to the end of the bitstring will be used.

        Raises ReadError if not enough bits are available.
        Raises ValueError if the format is not understood.

        See the docstring for 'read' for token examples.

        """
        if isinstance(fmt, numbers.Integral):
            fmt = f'bits:{fmt}'
        
        name, length = utils.parse_fmt(fmt)
        if self._pos + length > len(self):
            raise bitstring.ReadError(f"Not enough bits available to peek {fmt}")
        
        value, _ = self._readtoken(name, self._pos, length)
        return value

    def peeklist(self, fmt: Union[str, List[Union[int, str]]], **kwargs) -> List[Union[int, float, str, Bits, None]]:
        """Interpret next bits according to format string(s) and return list.

        fmt -- One or more integers or strings with comma separated tokens describing
               how to interpret the next bits in the bitstring.
        kwargs -- A dictionary or keyword-value pairs - the keywords used in the
                  format string will be replaced with their given value.

        The position in the bitstring is not changed. If not enough bits are
        available then all bits to the end of the bitstring will be used.

        Raises ReadError if not enough bits are available.
        Raises ValueError if the format is not understood.

        See the docstring for 'read' for token examples.

        """
        if isinstance(fmt, str):
            fmt = [f.strip() for f in fmt.split(',')]
        
        return_values = []
        pos = self._pos
        for f in fmt:
            if isinstance(f, numbers.Integral):
                f = f'bits:{f}'
            if isinstance(f, str):
                name, length = utils.parse_fmt(f)
                if name in kwargs:
                    length = kwargs[name]
            else:
                raise ValueError("Format must be a string or integer")
            
            if pos + length > len(self):
                raise bitstring.ReadError(f"Not enough bits available to peek {f}")
            
            value, new_pos = self._readtoken(name, pos, length)
            pos = new_pos
            if name != 'pad':
                return_values.append(value)
        
        return return_values

    def bytealign(self) -> int:
        """Align to next byte and return number of skipped bits.

        Raises ValueError if the end of the bitstring is reached before
        aligning to the next byte.

        """
        skipped = (8 - (self._pos % 8)) % 8
        if self._pos + skipped > len(self):
            raise ValueError("Cannot byte align - end of bitstring reached")
        self._pos += skipped
        return skipped

    @overload
    def __getitem__(self: TBits, key: slice, /) -> TBits:
        ...

    @overload
    def __getitem__(self: TBits, key: int, /) -> bool:
        ...

    def __getitem__(self: TBits, key: Union[slice, int], /) -> Union[TBits, bool]:
        """Return a new bitstring representing a slice of the current bitstring."""
        if isinstance(key, numbers.Integral):
            return bool(self._bitstore.getindex(key))
        bs = super().__new__(self.__class__)
        bs._bitstore = self._bitstore.getslice_withstep(key)
        bs._pos = 0
        return bs
    pos = property(_getbitpos, _setbitpos, doc='The position in the bitstring in bits. Read and write.\n                      ')
    bitpos = property(_getbitpos, _setbitpos, doc='The position in the bitstring in bits. Read and write.\n                      ')
    bytepos = property(_getbytepos, _setbytepos, doc='The position in the bitstring in bytes. Read and write.\n                      ')

class BitStream(ConstBitStream, bitstring.BitArray):
    """A container or stream holding a mutable sequence of bits

    Subclass of the ConstBitStream and BitArray classes. Inherits all of
    their methods.

    Methods:

    all() -- Check if all specified bits are set to 1 or 0.
    any() -- Check if any of specified bits are set to 1 or 0.
    append() -- Append a bitstring.
    bytealign() -- Align to next byte boundary.
    byteswap() -- Change byte endianness in-place.
    clear() -- Remove all bits from the bitstring.
    copy() -- Return a copy of the bitstring.
    count() -- Count the number of bits set to 1 or 0.
    cut() -- Create generator of constant sized chunks.
    endswith() -- Return whether the bitstring ends with a sub-string.
    find() -- Find a sub-bitstring in the current bitstring.
    findall() -- Find all occurrences of a sub-bitstring in the current bitstring.
    fromstring() -- Create a bitstring from a formatted string.
    insert() -- Insert a bitstring.
    invert() -- Flip bit(s) between one and zero.
    join() -- Join bitstrings together using current bitstring.
    overwrite() -- Overwrite a section with a new bitstring.
    peek() -- Peek at and interpret next bits as a single item.
    peeklist() -- Peek at and interpret next bits as a list of items.
    pp() -- Pretty print the bitstring.
    prepend() -- Prepend a bitstring.
    read() -- Read and interpret next bits as a single item.
    readlist() -- Read and interpret next bits as a list of items.
    readto() -- Read up to and including next occurrence of a bitstring.
    replace() -- Replace occurrences of one bitstring with another.
    reverse() -- Reverse bits in-place.
    rfind() -- Seek backwards to find a sub-bitstring.
    rol() -- Rotate bits to the left.
    ror() -- Rotate bits to the right.
    set() -- Set bit(s) to 1 or 0.
    split() -- Create generator of chunks split by a delimiter.
    startswith() -- Return whether the bitstring starts with a sub-bitstring.
    tobitarray() -- Return bitstring as a bitarray from the bitarray package.
    tobytes() -- Return bitstring as bytes, padding if needed.
    tofile() -- Write bitstring to file, padding if needed.
    unpack() -- Interpret bits using format string.

    Special methods:

    Mutating operators are available: [], <<=, >>=, +=, *=, &=, |= and ^=
    in addition to [], ==, !=, +, *, ~, <<, >>, &, | and ^.

    Properties:

    [GENERATED_PROPERTY_DESCRIPTIONS]

    len -- Length of the bitstring in bits.
    pos -- The current bit position in the bitstring.
    """
    __slots__ = ()

    def __init__(self, auto: Optional[Union[BitsType, int]]=None, /, length: Optional[int]=None, offset: Optional[int]=None, pos: int=0, **kwargs) -> None:
        """Either specify an 'auto' initialiser:
        A string of comma separated tokens, an integer, a file object,
        a bytearray, a boolean iterable or another bitstring.

        Or initialise via **kwargs with one (and only one) of:
        bin -- binary string representation, e.g. '0b001010'.
        hex -- hexadecimal string representation, e.g. '0x2ef'
        oct -- octal string representation, e.g. '0o777'.
        bytes -- raw data as a bytes object, for example read from a binary file.
        int -- a signed integer.
        uint -- an unsigned integer.
        float / floatbe -- a big-endian floating point number.
        bool -- a boolean (True or False).
        se -- a signed exponential-Golomb code.
        ue -- an unsigned exponential-Golomb code.
        sie -- a signed interleaved exponential-Golomb code.
        uie -- an unsigned interleaved exponential-Golomb code.
        floatle -- a little-endian floating point number.
        floatne -- a native-endian floating point number.
        bfloat / bfloatbe - a big-endian bfloat format 16-bit floating point number.
        bfloatle -- a little-endian bfloat format 16-bit floating point number.
        bfloatne -- a native-endian bfloat format 16-bit floating point number.
        intbe -- a signed big-endian whole byte integer.
        intle -- a signed little-endian whole byte integer.
        intne -- a signed native-endian whole byte integer.
        uintbe -- an unsigned big-endian whole byte integer.
        uintle -- an unsigned little-endian whole byte integer.
        uintne -- an unsigned native-endian whole byte integer.
        filename -- the path of a file which will be opened in binary read-only mode.

        Other keyword arguments:
        length -- length of the bitstring in bits, if needed and appropriate.
                  It must be supplied for all integer and float initialisers.
        offset -- bit offset to the data. These offset bits are
                  ignored and this is intended for use when
                  initialising using 'bytes' or 'filename'.
        pos -- Initial bit position, defaults to 0.

        """
        ConstBitStream.__init__(self, auto, length, offset, pos, **kwargs)
        if self._bitstore.immutable:
            self._bitstore = self._bitstore._copy()
            self._bitstore.immutable = False

    def __copy__(self) -> BitStream:
        """Return a new copy of the BitStream."""
        s_copy = object.__new__(BitStream)
        s_copy._pos = 0
        s_copy._bitstore = self._bitstore.copy()
        return s_copy

    def __iadd__(self, bs: BitsType, /) -> BitStream:
        """Append to current bitstring. Return self.

        bs -- the bitstring to append.

        The current bit position will be moved to the end of the BitStream.
        """
        self._append(bs)
        self._pos = len(self)
        return self

    def prepend(self, bs: BitsType, /) -> None:
        """Prepend a bitstring to the current bitstring.

        bs -- The bitstring to prepend.

        """
        bs = self.__class__._create_from_bitstype(bs)
        self._addleft(bs)
        self._pos += len(bs)

    def __setitem__(self, /, key: Union[slice, int], value: BitsType) -> None:
        length_before = len(self)
        super().__setitem__(key, value)
        if len(self) != length_before:
            self._pos = 0
        return

    def __delitem__(self, /, key: Union[slice, int]) -> None:
        """Delete item or range.

        >>> a = BitStream('0x001122')
        >>> del a[8:16]
        >>> print a
        0x0022

        """
        length_before = len(self)
        self._bitstore.__delitem__(key)
        if len(self) != length_before:
            self._pos = 0

    def insert(self, bs: BitsType, /, pos: Optional[int]=None) -> None:
        """Insert bitstring at bit position pos.

        bs -- The bitstring to insert.
        pos -- The bit position to insert at.

        The current bit position will be moved to the end of the inserted section.
        Raises ValueError if pos < 0 or pos > len(self).

        """
        bs = self.__class__._create_from_bitstype(bs)
        if pos is None:
            pos = self._pos
        if pos < 0 or pos > len(self):
            raise ValueError("Invalid insert position")
        
        self._insert(bs, pos)
        self._pos = pos + len(bs)

    def replace(self, old: BitsType, new: BitsType, start: Optional[int]=None, end: Optional[int]=None, count: Optional[int]=None, bytealigned: Optional[bool]=None) -> int:
        """Replace all occurrences of old with new in place.

        Returns number of replacements made.

        old -- The bitstring to replace.
        new -- The replacement bitstring.
        start -- Any occurrences that start before this will not be replaced.
                 Defaults to 0.
        end -- Any occurrences that finish after this will not be replaced.
               Defaults to len(self).
        count -- The maximum number of replacements to make. Defaults to
                 replace all occurrences.
        bytealigned -- If True replacements will only be made on byte
                       boundaries.

        Raises ValueError if old is empty or if start or end are
        out of range.

        """
        old = self.__class__._create_from_bitstype(old)
        new = self.__class__._create_from_bitstype(new)
        if not old:
            raise ValueError("Cannot replace an empty bitstring")
        
        start, end = self._validate_slice(start, end)
        if bytealigned is None:
            bytealigned = bitstring.bitstring_options.bytealigned
        
        positions = list(self.findall(old, start, end, bytealigned))
        if count is not None:
            positions = positions[:count]
        
        if not positions:
            return 0
        
        newdata = self[:positions[0]]
        for i, pos in enumerate(positions):
            if i + 1 < len(positions):
                newdata += new + self[pos + len(old):positions[i + 1]]
            else:
                newdata += new + self[pos + len(old):]
        
        self._setbytes_unsafe(newdata.tobytes(), newdata.len)
        self._pos = min(self._pos, len(self))
        return len(positions)
