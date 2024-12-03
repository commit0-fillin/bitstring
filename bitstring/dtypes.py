from __future__ import annotations
import functools
from typing import Optional, Dict, Any, Union, Tuple, Callable
import inspect
import bitstring
from bitstring import utils
CACHE_SIZE = 256

class Dtype:
    """A data type class, representing a concrete interpretation of binary data.

    Dtype instances are immutable. They are often created implicitly elsewhere via a token string.

    >>> u12 = Dtype('uint', 12)  # length separate from token string.
    >>> float16 = Dtype('float16')  # length part of token string.
    >>> mxfp = Dtype('e3m2mxfp', scale=2 ** 6)  # dtype with scaling factor

    """
    _name: str
    _read_fn: Callable
    _set_fn: Callable
    _get_fn: Callable
    _return_type: Any
    _is_signed: bool
    _set_fn_needs_length: bool
    _variable_length: bool
    _bitlength: Optional[int]
    _bits_per_item: int
    _length: Optional[int]
    _scale: Union[None, float, int]

    def __new__(cls, token: Union[str, Dtype], /, length: Optional[int]=None, scale: Union[None, float, int]=None) -> Dtype:
        if isinstance(token, cls):
            return token
        if length is None:
            x = cls._new_from_token(token, scale)
            return x
        else:
            x = dtype_register.get_dtype(token, length, scale)
            return x

    @property
    def scale(self) -> Union[int, float, None]:
        """The multiplicative scale applied when interpreting the data."""
        return self._scale

    @property
    def name(self) -> str:
        """A string giving the name of the data type."""
        return self._name

    @property
    def length(self) -> int:
        """The length of the data type in units of bits_per_item. Set to None for variable length dtypes."""
        return self._length

    @property
    def bitlength(self) -> Optional[int]:
        """The number of bits needed to represent a single instance of the data type. Set to None for variable length dtypes."""
        return self._bitlength

    @property
    def bits_per_item(self) -> int:
        """The number of bits for each unit of length. Usually 1, but equals 8 for bytes type."""
        return self._bits_per_item

    @property
    def variable_length(self) -> bool:
        """If True then the length of the data type depends on the data being interpreted, and must not be specified."""
        return self._variable_length

    @property
    def return_type(self) -> Any:
        """The type of the value returned by the parse method, such as int, float or str."""
        return self._return_type

    @property
    def is_signed(self) -> bool:
        """If True then the data type represents a signed quantity."""
        return self._is_signed

    @property
    def set_fn(self) -> Optional[Callable]:
        """A function to set the value of the data type."""
        return self._set_fn

    @property
    def get_fn(self) -> Callable:
        """A function to get the value of the data type."""
        return self._get_fn

    @property
    def read_fn(self) -> Callable:
        """A function to read the value of the data type."""
        return self._read_fn

    def __hash__(self) -> int:
        return hash((self._name, self._length))

    def build(self, value: Any, /) -> bitstring.Bits:
        """Create a bitstring from a value.

        The value parameter should be of a type appropriate to the dtype.
        """
        if self._set_fn is None:
            raise NotImplementedError(f"Cannot build {self._name} dtype")
        
        if self._set_fn_needs_length:
            return self._set_fn(value, self._length)
        else:
            return self._set_fn(value)

    def parse(self, b: BitsType, /) -> Any:
        """Parse a bitstring to find its value.

        The b parameter should be a bitstring of the appropriate length, or an object that can be converted to a bitstring."""
        if isinstance(b, bitstring.Bits):
            bits = b
        else:
            bits = bitstring.Bits(b)
        
        if self._scale is not None:
            return self._scale * self._get_fn(bits)
        else:
            return self._get_fn(bits)

    def __str__(self) -> str:
        if self._scale is not None:
            return self.__repr__()
        hide_length = self._variable_length or dtype_register.names[self._name].allowed_lengths.only_one_value() or self._length is None
        length_str = '' if hide_length else str(self._length)
        return f'{self._name}{length_str}'

    def __repr__(self) -> str:
        hide_length = self._variable_length or dtype_register.names[self._name].allowed_lengths.only_one_value() or self._length is None
        length_str = '' if hide_length else ', ' + str(self._length)
        if self._scale is None:
            scale_str = ''
        else:
            try:
                e8m0 = bitstring.Bits(e8m0mxfp=self._scale)
            except ValueError:
                scale_str = f', scale={self._scale}'
            else:
                power_of_two = e8m0.uint - 127
                if power_of_two in [0, 1]:
                    scale_str = f', scale={self._scale}'
                else:
                    scale_str = f', scale=2 ** {power_of_two}'
        return f"{self.__class__.__name__}('{self._name}'{length_str}{scale_str})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Dtype):
            return self._name == other._name and self._length == other._length
        return False

class AllowedLengths:

    def __init__(self, value: Tuple[int, ...]=tuple()) -> None:
        if len(value) >= 3 and value[-1] is Ellipsis:
            step = value[1] - value[0]
            for i in range(1, len(value) - 1):
                if value[i] - value[i - 1] != step:
                    raise ValueError(f'Allowed length tuples must be equally spaced when final element is Ellipsis, but got {value}.')
            self.values = (value[0], value[1], Ellipsis)
        else:
            self.values = value

    def __str__(self) -> str:
        if self.values and self.values[-1] is Ellipsis:
            return f'({self.values[0]}, {self.values[1]}, ...)'
        return str(self.values)

    def __contains__(self, other: Any) -> bool:
        if not self.values:
            return True
        if self.values[-1] is Ellipsis:
            return (other - self.values[0]) % (self.values[1] - self.values[0]) == 0
        return other in self.values

class DtypeDefinition:
    """Represents a class of dtypes, such as uint or float, rather than a concrete dtype such as uint8.
    Not (yet) part of the public interface."""

    def __init__(self, name: str, set_fn, get_fn, return_type: Any=Any, is_signed: bool=False, bitlength2chars_fn=None, variable_length: bool=False, allowed_lengths: Tuple[int, ...]=tuple(), multiplier: int=1, description: str=''):
        if int(multiplier) != multiplier or multiplier <= 0:
            raise ValueError('multiplier must be an positive integer')
        if variable_length and allowed_lengths:
            raise ValueError("A variable length dtype can't have allowed lengths.")
        if variable_length and set_fn is not None and ('length' in inspect.signature(set_fn).parameters):
            raise ValueError("A variable length dtype can't have a set_fn which takes a length.")
        self.name = name
        self.description = description
        self.return_type = return_type
        self.is_signed = is_signed
        self.variable_length = variable_length
        self.allowed_lengths = AllowedLengths(allowed_lengths)
        self.multiplier = multiplier
        self.set_fn_needs_length = set_fn is not None and 'length' in inspect.signature(set_fn).parameters
        self.set_fn = set_fn
        if self.allowed_lengths.values:

            def allowed_length_checked_get_fn(bs):
                if len(bs) not in self.allowed_lengths:
                    if self.allowed_lengths.only_one_value():
                        raise bitstring.InterpretError(f"'{self.name}' dtypes must have a length of {self.allowed_lengths.values[0]}, but received a length of {len(bs)}.")
                    else:
                        raise bitstring.InterpretError(f"'{self.name}' dtypes must have a length in {self.allowed_lengths}, but received a length of {len(bs)}.")
                return get_fn(bs)
            self.get_fn = allowed_length_checked_get_fn
        else:
            self.get_fn = get_fn
        if not self.variable_length:
            if self.allowed_lengths.only_one_value():

                def read_fn(bs, start):
                    return self.get_fn(bs[start:start + self.allowed_lengths.values[0]])
            else:

                def read_fn(bs, start, length):
                    if len(bs) < start + length:
                        raise bitstring.ReadError(f'Needed a length of at least {length} bits, but only {len(bs) - start} bits were available.')
                    return self.get_fn(bs[start:start + length])
            self.read_fn = read_fn
        else:

            def length_checked_get_fn(bs):
                x, length = get_fn(bs)
                if length != len(bs):
                    raise ValueError
                return x
            self.get_fn = length_checked_get_fn

            def read_fn(bs, start):
                try:
                    x, length = get_fn(bs[start:])
                except bitstring.InterpretError:
                    raise bitstring.ReadError
                return (x, start + length)
            self.read_fn = read_fn
        self.bitlength2chars_fn = bitlength2chars_fn

    def __repr__(self) -> str:
        s = f"{self.__class__.__name__}(name='{self.name}', description='{self.description}', return_type={self.return_type.__name__}, "
        s += f'is_signed={self.is_signed}, set_fn_needs_length={self.set_fn_needs_length}, allowed_lengths={self.allowed_lengths!s}, multiplier={self.multiplier})'
        return s

class Register:
    """A singleton class that holds all the DtypeDefinitions. Not (yet) part of the public interface."""
    _instance: Optional[Register] = None
    names: Dict[str, DtypeDefinition] = {}

    def __new__(cls) -> Register:
        if cls._instance is None:
            cls._instance = super(Register, cls).__new__(cls)
        return cls._instance

    @classmethod
    def __getitem__(cls, name: str) -> DtypeDefinition:
        return cls.names[name]

    @classmethod
    def __delitem__(cls, name: str) -> None:
        del cls.names[name]

    def __repr__(self) -> str:
        s = [f'{'key':<12}:{'name':^12}{'signed':^8}{'set_fn_needs_length':^23}{'allowed_lengths':^16}{'multiplier':^12}{'return_type':<13}']
        s.append('-' * 85)
        for key in self.names:
            m = self.names[key]
            allowed = '' if not m.allowed_lengths else m.allowed_lengths
            ret = 'None' if m.return_type is None else m.return_type.__name__
            s.append(f'{key:<12}:{m.name:>12}{m.is_signed:^8}{m.set_fn_needs_length:^16}{allowed!s:^16}{m.multiplier:^12}{ret:<13} # {m.description}')
        return '\n'.join(s)
dtype_register = Register()
