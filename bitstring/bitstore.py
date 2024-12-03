from __future__ import annotations
import bitarray
from bitstring.exceptions import CreationError
from typing import Union, Iterable, Optional, overload, Iterator, Any

class BitStore:
    """A light wrapper around bitarray that does the LSB0 stuff"""
    __slots__ = ('_bitarray', 'modified_length', 'immutable')

    def __init__(self, initializer: Union[int, bitarray.bitarray, str, None]=None, immutable: bool=False) -> None:
        self._bitarray = bitarray.bitarray(initializer)
        self.immutable = immutable
        self.modified_length = None

    def __iadd__(self, other: BitStore, /) -> BitStore:
        self._bitarray += other._bitarray
        return self

    def __add__(self, other: BitStore, /) -> BitStore:
        bs = self._copy()
        bs += other
        return bs

    def __eq__(self, other: Any, /) -> bool:
        return self._bitarray == other._bitarray

    def __and__(self, other: BitStore, /) -> BitStore:
        return BitStore(self._bitarray & other._bitarray)

    def __or__(self, other: BitStore, /) -> BitStore:
        return BitStore(self._bitarray | other._bitarray)

    def __xor__(self, other: BitStore, /) -> BitStore:
        return BitStore(self._bitarray ^ other._bitarray)

    def __iand__(self, other: BitStore, /) -> BitStore:
        self._bitarray &= other._bitarray
        return self

    def __ior__(self, other: BitStore, /) -> BitStore:
        self._bitarray |= other._bitarray
        return self

    def __ixor__(self, other: BitStore, /) -> BitStore:
        self._bitarray ^= other._bitarray
        return self

    def __iter__(self) -> Iterable[bool]:
        for i in range(len(self)):
            yield self.getindex(i)

    def _copy(self) -> BitStore:
        """Always creates a copy, even if instance is immutable."""
        new_bitstore = BitStore()
        new_bitstore._bitarray = self._bitarray.copy()
        new_bitstore.modified_length = self.modified_length
        new_bitstore.immutable = False  # The copy is always mutable
        return new_bitstore

    def __getitem__(self, item: Union[int, slice], /) -> Union[int, BitStore]:
        raise NotImplementedError

    def __len__(self) -> int:
        return self.modified_length if self.modified_length is not None else len(self._bitarray)
