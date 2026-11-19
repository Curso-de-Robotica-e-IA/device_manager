from collections.abc import Iterator, KeysView, MutableMapping
from typing import Any, TypeVar

T = TypeVar('T')


class ObjectManager(MutableMapping[str, T]):
    """Strict `MutableMapping[str, T]` container enforcing string keys and
    homogeneous object types across all write operations.
    """

    def __init__(self) -> None:
        self.__objects: dict[str, T] = {}

    def _validate_key(self, key: Any) -> str:
        if not isinstance(key, str):
            raise TypeError(f'Key of type {type(key)} not allowed')
        return key

    def _validate_value(self, obj: T) -> None:
        if self.__objects:
            expected_type = type(next(iter(self.__objects.values())))
            if not isinstance(obj, expected_type):
                raise TypeError(f'Object of type {type(obj)} not allowed')

    def keys(self) -> KeysView[str]:
        return self.__objects.keys()

    def add(self, key: Any, obj: T) -> None:
        self[key] = obj

    def remove(self, key: Any) -> None:
        validated_key = self._validate_key(key)
        self.__objects.pop(validated_key, None)

    def get(self, key: Any, default: Any = None) -> T | Any:
        validated_key = self._validate_key(key)
        return self.__objects.get(validated_key, default)

    def edit(self, key: Any, new_obj: T) -> None:
        validated_key = self._validate_key(key)
        if validated_key in self.__objects:
            self._validate_value(new_obj)
            self.__objects[validated_key] = new_obj

    def __len__(self) -> int:
        return len(self.__objects)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__objects)

    def __getitem__(self, key: str) -> T:
        validated_key = self._validate_key(key)
        return self.__objects[validated_key]

    def __setitem__(self, key: str, obj: T) -> None:
        validated_key = self._validate_key(key)
        self._validate_value(obj)
        self.__objects[validated_key] = obj

    def __delitem__(self, key: str) -> None:
        validated_key = self._validate_key(key)
        del self.__objects[validated_key]

    def __contains__(self, key: object) -> bool:
        return key in self.__objects
