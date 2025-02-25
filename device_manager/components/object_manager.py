from types import MappingProxyType
from typing import Dict, Generic, Optional, TypeVar

T = TypeVar('T')


class ObjectManager(Generic[T]):
    """Generic object manager class to manage objects of a specific type.
    The class provides methods to add, remove, get, edit, and iterate over
    objects of a specific type.

    The class is generic and can be used to manage objects of any type, but
    the type of the objects must be consistent. The class will raise a
    TypeError if an object of a different type is added to the manager.
    """

    def __init__(self):
        self.__objects: Dict[str, T] = dict()

    def keys(self) -> MappingProxyType:
        """Get the keys of the objects in the manager.

        Returns:
            MappingProxyType: A read-only view of the keys in the manager.
        """
        return self.__objects.keys()

    def add(self, key: str, obj: T):
        """Add an object to the manager.

        Args:
            key (str): The key to associate with the object.
            obj (T): The object to add to the manager.

        Raises:
            TypeError: If the key is not a string.
            TypeError: If the object is not of the same type as the objects
                already in the manager.
        """
        if not isinstance(key, str):
            raise TypeError(f"Key of type {type(key)} not allowed")
        if len(self.__objects) > 0:
            if not isinstance(obj, type(list(self.__objects.values())[0])):
                raise TypeError(f"Object of type {type(obj)} not allowed")
        self[key] = obj

    def remove(self, key: str):
        """Remove an object from the manager.

        Args:
            key (str): The key of the object to remove.
        """
        if key in self.__objects:
            del self[key]

    def get(self, key: str) -> T:
        """Get an object from the manager.

        Args:
            key (str): The key of the object to get.

        Returns:
            T: The object associated with the key.
        """
        return self[key]

    def edit(self, key: str, new_obj: T):
        """Edit an object in the manager.

        Args:
            key (str): The key of the object to edit.
            new_obj (T): The new object to replace the existing object.
        """
        if key in self.__objects:
            self[key] = new_obj

    def __len__(self):
        """Get the number of objects in the manager.

        Returns:
            int: The number of objects in the manager.
        """
        return len(self.__objects)

    def __iter__(self):
        """Iterate over the objects in the manager."""
        return iter(self.__objects.values())

    def __getitem__(self, key: str) -> Optional[T]:
        """Get an object from the manager.

        Args:
            key (str): The key of the object to get.

        Returns:
            T: The object associated with the key.
        """
        try:
            return self.__objects[key]
        except KeyError:
            return None

    def __setitem__(self, key: str, obj: T):
        """Set an object in the manager.

        Args:
            key (str): The key to associate with the object.
            obj (T): The object to add to the manager.
        """
        self.__objects[key] = obj

    def __delitem__(self, key: str):
        """Remove an object from the manager.

        Args:
            key (str): The key of the object to remove.
        """
        del self.__objects[key]

    def __contains__(self, key: str) -> bool:
        """Check if the manager contains an object with the specified key.

        Args:
            key (str): The key to check for in the manager.

        Returns:
            bool: True if the manager contains the key, False otherwise.
        """
        return key in self.__objects
