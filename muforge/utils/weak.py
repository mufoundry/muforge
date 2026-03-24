from collections.abc import Iterable, MutableSequence
from typing import Any, Callable, Iterator, TypeVar, overload
import weakref

T = TypeVar("T")
WeakRefT = TypeVar("WeakRefT")


class WeakList(MutableSequence[T]):
    def __init__(self, init: list[T] | None = None) -> None:
        self._refs: list[weakref.ref[T]] = []
        self._callback: Callable[[Any], Any] = self._remove_dead_ref
        if init:
            self.extend(init)

    def _remove_dead_ref(self, ref: Any) -> None:
        try:
            self._refs.remove(ref)
        except ValueError:
            pass

    def _get_valid_refs(self) -> list[weakref.ref[T]]:
        dead = []
        for ref in self._refs:
            if ref() is None:
                dead.append(ref)
        for ref in dead:
            self._refs.remove(ref)
        return list(self._refs)

    def __len__(self) -> int:
        return len(self._get_valid_refs())

    def __bool__(self) -> bool:
        return len(self) > 0

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> "WeakList[T]": ...
    def __getitem__(self, index: int | slice) -> T | "WeakList[T]":
        valid_refs = self._get_valid_refs()
        if isinstance(index, slice):
            items = [r() for r in valid_refs[index]]
            return WeakList([x for x in items if x is not None])
        result = valid_refs[index]
        if result is None:
            raise IndexError("list index out of range")
        return result()  # type: ignore[return-value]

    @overload
    def __setitem__(self, index: int, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...
    def __setitem__(self, index: int | slice, value: T | Iterable[T]) -> None:
        all_refs = self._get_valid_refs()
        if isinstance(index, slice):
            assert isinstance(value, (list, tuple))
            value_refs = [weakref.ref(v, self._callback) for v in value]
            all_refs[index] = value_refs  # type: ignore[assignment]
        else:
            value_ref = weakref.ref(value, self._callback)
            all_refs[index] = value_ref  # type: ignore[assignment]
        self._refs = all_refs

    def __delitem__(self, index: int | slice) -> None:
        all_refs = self._get_valid_refs()
        del all_refs[index]
        self._refs = all_refs

    def __iter__(self) -> Iterator[T]:
        refs = self._get_valid_refs()
        for ref in refs:
            obj = ref()
            if obj is not None:
                yield obj

    def __contains__(self, item: object) -> bool:
        for ref in self._get_valid_refs():
            obj = ref()
            if obj is item:
                return True
        return False

    def __repr__(self) -> str:
        return f"WeakList({list(self)})"

    def __str__(self) -> str:
        return str(list(self))

    def append(self, value: T) -> None:
        self._refs.append(weakref.ref(value, self._callback))

    def insert(self, index: int, value: T) -> None:
        valid_refs = self._get_valid_refs()
        valid_refs.insert(index, weakref.ref(value, self._callback))
        self._refs = valid_refs

    def extend(self, values: Iterable[T]) -> None:
        for item in values:
            self.append(item)

    def pop(self, index: int = -1) -> T:
        valid_refs = self._get_valid_refs()
        if not valid_refs:
            raise IndexError("pop from empty WeakList")
        result_ref = valid_refs.pop(index)
        self._refs = valid_refs
        result = result_ref()
        if result is None:
            raise IndexError("pop from empty WeakList")
        return result

    def remove(self, value: T) -> None:
        for i, ref in enumerate(self._get_valid_refs()):
            obj = ref()
            if obj is value:
                del self[i]
                return
        raise ValueError(f"{value!r} not in WeakList")

    def clear(self) -> None:
        self._refs.clear()

    def index(self, value: T, start: int = 0, stop: int | None = None) -> int:
        refs = self._get_valid_refs()
        if stop is None:
            stop = len(refs)
        for i in range(start, stop):
            if refs[i]() is value:
                return i
        raise ValueError(f"{value!r} not in WeakList")

    def count(self, value: object) -> int:
        return sum(1 for ref in self._get_valid_refs() if ref() is value)

    def copy(self) -> "WeakList[T]":
        return WeakList(list(self))

    def reverse(self) -> None:
        valid_refs = self._get_valid_refs()
        valid_refs.reverse()
        self._refs = valid_refs