from __future__ import annotations
import math
import numbers
from collections.abc import Sized
from bitstring.exceptions import CreationError
from typing import Union, List, Iterable, Any, Optional, BinaryIO, overload, TextIO
from bitstring.bits import Bits, BitsType
from bitstring.bitarray_ import BitArray
from bitstring.dtypes import Dtype, dtype_register
from bitstring import utils
from bitstring.bitstring_options import Options, Colour
import copy
import array
import operator
import io
import sys
ElementType = Union[float, str, int, bytes, bool, Bits]
options = Options()

class Array:
    """Return an Array whose elements are initialised according to the fmt string.
    The dtype string can be typecode as used in the struct module or any fixed-length bitstring
    format.

    a = Array('>H', [1, 15, 105])
    b = Array('int5', [-9, 0, 4])

    The Array data is stored compactly as a BitArray object and the Array behaves very like
    a list of items of the given format. Both the Array data and fmt properties can be freely
    modified after creation. If the data length is not a multiple of the fmt length then the
    Array will have 'trailing_bits' which will prevent some methods from appending to the
    Array.

    Methods:

    append() -- Append a single item to the end of the Array.
    byteswap() -- Change byte endianness of all items.
    count() -- Count the number of occurences of a value.
    extend() -- Append new items to the end of the Array from an iterable.
    fromfile() -- Append items read from a file object.
    insert() -- Insert an item at a given position.
    pop() -- Remove and return an item.
    pp() -- Pretty print the Array.
    reverse() -- Reverse the order of all items.
    tobytes() -- Return Array data as bytes object, padding with zero bits at the end if needed.
    tofile() -- Write Array data to a file, padding with zero bits at the end if needed.
    tolist() -- Return Array items as a list.

    Special methods:

    Also available are the operators [], ==, !=, +, *, <<, >>, &, |, ^,
    plus the mutating operators [], +=, *=, <<=, >>=, &=, |=, ^=.

    Properties:

    data -- The BitArray binary data of the Array. Can be freely modified.
    dtype -- The format string or typecode. Can be freely modified.
    itemsize -- The length *in bits* of a single item. Read only.
    trailing_bits -- If the data length is not a multiple of the fmt length, this BitArray
                     gives the leftovers at the end of the data.


    """

    def __init__(self, dtype: Union[str, Dtype], initializer: Optional[Union[int, Array, array.array, Iterable, Bits, bytes, bytearray, memoryview, BinaryIO]]=None, trailing_bits: Optional[BitsType]=None) -> None:
        self.data = BitArray()
        if isinstance(dtype, Dtype) and dtype.scale == 'auto':
            if isinstance(initializer, (int, Bits, bytes, bytearray, memoryview, BinaryIO)):
                raise TypeError("An Array with an 'auto' scale factor can only be created from an iterable of values.")
            auto_scale = self._calculate_auto_scale(initializer, dtype.name, dtype.length)
            dtype = Dtype(dtype.name, dtype.length, scale=auto_scale)
        try:
            self._set_dtype(dtype)
        except ValueError as e:
            raise CreationError(e)
        if isinstance(initializer, numbers.Integral):
            self.data = BitArray(initializer * self._dtype.bitlength)
        elif isinstance(initializer, (Bits, bytes, bytearray, memoryview)):
            self.data += initializer
        elif isinstance(initializer, io.BufferedReader):
            self.fromfile(initializer)
        elif initializer is not None:
            self.extend(initializer)
        if trailing_bits is not None:
            self.data += BitArray._create_from_bitstype(trailing_bits)
    _largest_values = None

    def _create_element(self, value: ElementType) -> Bits:
        """Create Bits from value according to the token_name and token_length"""
        return self._dtype.build(value)

    def __len__(self) -> int:
        return len(self.data) // self._dtype.length

    @overload
    def __getitem__(self, key: slice) -> Array:
        ...

    @overload
    def __getitem__(self, key: int) -> ElementType:
        ...

    def __getitem__(self, key: Union[slice, int]) -> Union[Array, ElementType]:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if step != 1:
                d = BitArray()
                for s in range(start * self._dtype.length, stop * self._dtype.length, step * self._dtype.length):
                    d.append(self.data[s:s + self._dtype.length])
                a = self.__class__(self._dtype)
                a.data = d
                return a
            else:
                a = self.__class__(self._dtype)
                a.data = self.data[start * self._dtype.length:stop * self._dtype.length]
                return a
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError(f'Index {key} out of range for Array of length {len(self)}.')
            return self._dtype.read_fn(self.data, start=self._dtype.length * key)

    @overload
    def __setitem__(self, key: slice, value: Iterable[ElementType]) -> None:
        ...

    @overload
    def __setitem__(self, key: int, value: ElementType) -> None:
        ...

    def __setitem__(self, key: Union[slice, int], value: Union[Iterable[ElementType], ElementType]) -> None:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if not isinstance(value, Iterable):
                raise TypeError('Can only assign an iterable to a slice.')
            if step == 1:
                new_data = BitArray()
                for x in value:
                    new_data += self._create_element(x)
                self.data[start * self._dtype.length:stop * self._dtype.length] = new_data
                return
            items_in_slice = len(range(start, stop, step))
            if not isinstance(value, Sized):
                value = list(value)
            if len(value) == items_in_slice:
                for s, v in zip(range(start, stop, step), value):
                    self.data.overwrite(self._create_element(v), s * self._dtype.length)
            else:
                raise ValueError(f"Can't assign {len(value)} values to an extended slice of length {items_in_slice}.")
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError(f'Index {key} out of range for Array of length {len(self)}.')
            start = self._dtype.length * key
            self.data.overwrite(self._create_element(value), start)
            return

    def __delitem__(self, key: Union[slice, int]) -> None:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if step == 1:
                self.data.__delitem__(slice(start * self._dtype.length, stop * self._dtype.length))
                return
            r = reversed(range(start, stop, step)) if step > 0 else range(start, stop, step)
            for s in r:
                self.data.__delitem__(slice(s * self._dtype.length, (s + 1) * self._dtype.length))
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError
            start = self._dtype.length * key
            del self.data[start:start + self._dtype.length]

    def __repr__(self) -> str:
        list_str = f'{self.tolist()}'
        trailing_bit_length = len(self.data) % self._dtype.length
        final_str = '' if trailing_bit_length == 0 else ', trailing_bits=' + repr(self.data[-trailing_bit_length:])
        return f"Array('{self._dtype}', {list_str}{final_str})"

    def astype(self, dtype: Union[str, Dtype]) -> Array:
        """Return Array with elements of new dtype, initialised from current Array."""
        new_dtype = Dtype(dtype)
        new_array = Array(new_dtype)
        new_array.data = BitArray()
        for item in self:
            new_array.data += new_dtype.build(item)
        return new_array

    def insert(self, i: int, x: ElementType) -> None:
        """Insert a new element into the Array at position i."""
        if i < 0:
            i += len(self)
        if i < 0 or i > len(self):
            raise IndexError("Array index out of range")
        element = self._create_element(x)
        self.data.insert(element, i * self._dtype.length)

    def pop(self, i: int=-1) -> ElementType:
        """Return and remove an element of the Array.

        Default is to return and remove the final element.
        """
        if i < 0:
            i += len(self)
        if i < 0 or i >= len(self):
            raise IndexError("Array index out of range")
        start = i * self._dtype.length
        end = start + self._dtype.length
        element = self.data[start:end]
        del self.data[start:end]
        return self._dtype.parse(element)

    def byteswap(self) -> None:
        """Change the endianness in-place of all items in the Array.

        If the Array format is not a whole number of bytes a ValueError will be raised.
        """
        if self._dtype.length % 8 != 0:
            raise ValueError("Array format is not a whole number of bytes")
        bytes_per_element = self._dtype.length // 8
        for i in range(len(self)):
            start = i * self._dtype.length
            end = start + self._dtype.length
            element = self.data[start:end]
            swapped = element.byteswap(bytes_per_element)
            self.data.overwrite(swapped, start)

    def count(self, value: ElementType) -> int:
        """Return count of Array items that equal value.

        value -- The quantity to compare each Array element to. Type should be appropriate for the Array format.

        For floating point types using a value of float('nan') will count the number of elements that are NaN.
        """
        count = 0
        for item in self:
            if isinstance(value, float) and value != value:  # Check for NaN
                if item != item:
                    count += 1
            elif item == value:
                count += 1
        return count

    def tobytes(self) -> bytes:
        """Return the Array data as a bytes object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.
        """
        return self.data.tobytes()

    def tofile(self, f: BinaryIO) -> None:
        """Write the Array data to a file object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.
        """
        self.data.tofile(f)

    def pp(self, fmt: Optional[str]=None, width: int=120, show_offset: bool=True, stream: TextIO=sys.stdout) -> None:
        """Pretty-print the Array contents.

        fmt -- Data format string. Defaults to current Array dtype.
        width -- Max width of printed lines in characters. Defaults to 120. A single group will always
                 be printed per line even if it exceeds the max width.
        show_offset -- If True shows the element offset in the first column of each line.
        stream -- A TextIO object with a write() method. Defaults to sys.stdout.
        """
        if fmt is None:
            fmt = str(self._dtype)
        
        items_per_line = max(1, width // (len(str(self[0])) + 1))
        for i, item in enumerate(self):
            if i % items_per_line == 0:
                if i > 0:
                    stream.write('\n')
                if show_offset:
                    stream.write(f'{i:4d}: ')
            stream.write(f'{item:{fmt}} ')
        stream.write('\n')

    def equals(self, other: Any) -> bool:
        """Return True if format and all Array items are equal."""
        if not isinstance(other, Array):
            return False
        if self._dtype != other._dtype:
            return False
        if len(self) != len(other):
            return False
        return all(a == b for a, b in zip(self, other))

    def __iter__(self) -> Iterable[ElementType]:
        start = 0
        for _ in range(len(self)):
            yield self._dtype.read_fn(self.data, start=start)
            start += self._dtype.length

    def __copy__(self) -> Array:
        a_copy = self.__class__(self._dtype)
        a_copy.data = copy.copy(self.data)
        return a_copy

    def _apply_op_to_all_elements(self, op, value: Union[int, float, None], is_comparison: bool=False) -> Array:
        """Apply op with value to each element of the Array and return a new Array"""
        result = Array(self._dtype)
        for item in self:
            if value is None:
                new_value = op(item)
            else:
                new_value = op(item, value)
            if is_comparison:
                new_value = int(new_value)
            result.append(new_value)
        return result

    def _apply_op_to_all_elements_inplace(self, op, value: Union[int, float]) -> Array:
        """Apply op with value to each element of the Array in place."""
        for i in range(len(self)):
            self[i] = op(self[i], value)
        return self

    def _apply_bitwise_op_to_all_elements(self, op, value: BitsType) -> Array:
        """Apply op with value to each element of the Array as an unsigned integer and return a new Array"""
        result = Array(self._dtype)
        value_bits = Bits(value)
        for item in self:
            item_bits = self._dtype.build(item)
            new_bits = op(item_bits, value_bits)
            result.append(self._dtype.parse(new_bits))
        return result

    def _apply_bitwise_op_to_all_elements_inplace(self, op, value: BitsType) -> Array:
        """Apply op with value to each element of the Array as an unsigned integer in place."""
        value_bits = Bits(value)
        for i in range(len(self)):
            item_bits = self._dtype.build(self[i])
            new_bits = op(item_bits, value_bits)
            self[i] = self._dtype.parse(new_bits)
        return self

    @classmethod
    def _promotetype(cls, type1: Dtype, type2: Dtype) -> Dtype:
        """When combining types which one wins?

        1. We only deal with types representing floats or integers.
        2. One of the two types gets returned. We never create a new one.
        3. Floating point types always win against integer types.
        4. Signed integer types always win against unsigned integer types.
        5. Longer types win against shorter types.
        6. In a tie the first type wins against the second type.
        """
        if 'float' in type1.name:
            return type1
        if 'float' in type2.name:
            return type2
        
        if type1.is_signed and not type2.is_signed:
            return type1
        if type2.is_signed and not type1.is_signed:
            return type2
        
        if type1.bitlength > type2.bitlength:
            return type1
        if type2.bitlength > type1.bitlength:
            return type2
        
        return type1

    def __add__(self, other: Union[int, float, Array]) -> Array:
        """Add int or float to all elements."""
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.add, other)
        return self._apply_op_to_all_elements(operator.add, other)

    def __iadd__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.add, other)
        return self._apply_op_to_all_elements_inplace(operator.add, other)

    def __isub__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.sub, other)
        return self._apply_op_to_all_elements_inplace(operator.sub, other)

    def __sub__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.sub, other)
        return self._apply_op_to_all_elements(operator.sub, other)

    def __mul__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.mul, other)
        return self._apply_op_to_all_elements(operator.mul, other)

    def __imul__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.mul, other)
        return self._apply_op_to_all_elements_inplace(operator.mul, other)

    def __floordiv__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.floordiv, other)
        return self._apply_op_to_all_elements(operator.floordiv, other)

    def __ifloordiv__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.floordiv, other)
        return self._apply_op_to_all_elements_inplace(operator.floordiv, other)

    def __truediv__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.truediv, other)
        return self._apply_op_to_all_elements(operator.truediv, other)

    def __itruediv__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.truediv, other)
        return self._apply_op_to_all_elements_inplace(operator.truediv, other)

    def __rshift__(self, other: Union[int, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.rshift, other)
        return self._apply_op_to_all_elements(operator.rshift, other)

    def __lshift__(self, other: Union[int, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.lshift, other)
        return self._apply_op_to_all_elements(operator.lshift, other)

    def __irshift__(self, other: Union[int, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.rshift, other)
        return self._apply_op_to_all_elements_inplace(operator.rshift, other)

    def __ilshift__(self, other: Union[int, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.lshift, other)
        return self._apply_op_to_all_elements_inplace(operator.lshift, other)

    def __mod__(self, other: Union[int, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.mod, other)
        return self._apply_op_to_all_elements(operator.mod, other)

    def __imod__(self, other: Union[int, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.mod, other)
        return self._apply_op_to_all_elements_inplace(operator.mod, other)

    def __and__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.iand, other)

    def __iand__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements_inplace(operator.iand, other)

    def __or__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.ior, other)

    def __ior__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements_inplace(operator.ior, other)

    def __xor__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.ixor, other)

    def __ixor__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements_inplace(operator.ixor, other)

    def __rmul__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements(operator.mul, other)

    def __radd__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements(operator.add, other)

    def __rsub__(self, other: Union[int, float]) -> Array:
        neg = self._apply_op_to_all_elements(operator.neg, None)
        return neg._apply_op_to_all_elements(operator.add, other)

    def __rand__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.iand, other)

    def __ror__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.ior, other)

    def __rxor__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.ixor, other)

    def __lt__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.lt, other, is_comparison=True)
        return self._apply_op_to_all_elements(operator.lt, other, is_comparison=True)

    def __gt__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.gt, other, is_comparison=True)
        return self._apply_op_to_all_elements(operator.gt, other, is_comparison=True)

    def __ge__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.ge, other, is_comparison=True)
        return self._apply_op_to_all_elements(operator.ge, other, is_comparison=True)

    def __le__(self, other: Union[int, float, Array]) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.le, other, is_comparison=True)
        return self._apply_op_to_all_elements(operator.le, other, is_comparison=True)

    def __eq__(self, other: Any) -> Array:
        return self._eq_ne(operator.eq, other)

    def __ne__(self, other: Any) -> Array:
        return self._eq_ne(operator.ne, other)

    def __neg__(self):
        return self._apply_op_to_all_elements(operator.neg, None)

    def __abs__(self):
        return self._apply_op_to_all_elements(operator.abs, None)
