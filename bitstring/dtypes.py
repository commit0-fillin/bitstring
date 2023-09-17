from __future__ import annotations

import functools
from bitstring.exceptions import InterpretError
from bitstring.bits import Bits
from typing import Optional, Dict


class Dtype:

    def __init__(self, name: str, length: Optional[int], set_fn, get_fn, is_integer, is_float, is_signed,
                 is_unknown_length, is_fixed_length) -> None:
        self.name = name
        self.length = length
        self.get = functools.partial(get_fn, length=length)
        self.set = functools.partial(set_fn, length=length)
        self.is_integer = is_integer
        self.is_signed = is_signed
        self.is_float = is_float
        self.is_fixed_length = is_fixed_length
        self.is_unknown_length = is_unknown_length

    def __str__(self) -> str:
        length_str = '' if (self.length == 0 or self.is_fixed_length) else str(self.length)
        return f"{self.name}{length_str}"

    def __repr__(self) -> str:
        s = self.__str__()
        return f"{self.__class__.__name__}('{s}')"


class MetaDtype:
    # Represents a class of dtypes, such as uint or float, rather than a concrete dtype such as uint8.

    def __init__(self, name: str, set_fn, get_fn, is_integer: bool, is_float: bool, is_signed: bool,
                 is_unknown_length: bool, length: Optional[int] = None):
        # Consistency checks
        if is_unknown_length and length is not None:
            raise ValueError("Can't set is_unknown_length and give a value for length.")
        if is_float and is_integer:
            raise ValueError("Can't have type that is both float and integer.")

        self.name = name
        self.is_float = is_float
        self.is_integer = is_integer
        self.is_signed = is_signed
        self.is_fixed_length = length is not None
        self.is_unknown_length = is_unknown_length
        self.length = length

        self.set = set_fn
        self.get = get_fn

    def getDtype(self, length: Optional[int] = None) -> Dtype:
        if length is None:
            if not self.is_fixed_length:
                raise ValueError("No length given for dtype, and meta type is not fixed length.")
            d = Dtype(self.name, None, self.set, self.get, self.is_integer, self.is_float, self.is_signed,
                             self.is_unknown_length, self.is_fixed_length)
            return d
        if self.is_unknown_length:
            raise ValueError("Length shouldn't be supplied for dtypes that are variable length.")
        if self.is_fixed_length:
            if length != 0 and length != self.length:
                raise ValueError  # TODO
            length = self.length
        d = Dtype(self.name, length, self.set, self.get, self.is_integer, self.is_float, self.is_signed,
                  self.is_unknown_length, self.is_fixed_length)
        return d


class Register:

    _instance = None

    def __new__(cls) -> Register:
        if cls._instance is None:
            cls._instance = super(Register, cls).__new__(cls)
            cls.name_to_meta_dtype: Dict[str, MetaDtype] = {}
        return cls._instance

    @classmethod
    def add_meta_dtype(cls, meta_dtype: MetaDtype):
        cls.name_to_meta_dtype[meta_dtype.name] = meta_dtype

    @classmethod
    def add_meta_dtype_alias(cls, name: str, alias: str):
        cls.name_to_meta_dtype[alias] = cls.name_to_meta_dtype[name]

    @classmethod
    def get_dtype(cls, name: str, length: Optional[int]) -> Dtype:
        try:
            meta_type = cls.name_to_meta_dtype[name]
        except KeyError:
            raise ValueError
        d = meta_type.getDtype(length)
        # Test if the length makes sense by trying out the getter.  # TODO: Optimise!
        if length != 0:
            temp = Bits(length)
            try:
                _ = d.get(temp, 0)
            except InterpretError as e:
                raise ValueError(f"Invalid Dtype: {e.msg}")
        return d




