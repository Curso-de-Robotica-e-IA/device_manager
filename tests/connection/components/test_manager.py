from collections.abc import MutableMapping

import pytest

from device_manager.components.object_manager import ObjectManager


@pytest.mark.parametrize(
    ('key', 'value'),
    [
        ('one', 1),
        ('two', 2),
        ('three', 3),
    ],
)
def test_object_manager_add(key: str, value: int) -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add(key, value)

    assert manager[key] == value


def test_object_manager_key_not_string() -> None:
    manager: ObjectManager[int] = ObjectManager()
    with pytest.raises(TypeError):
        manager.add(1, 1)


def test_object_manager_holds_just_one_type_on_add_and_setitem() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)
    with pytest.raises(TypeError):
        manager.add('two', '2')  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        manager['two'] = '2'  # type: ignore[assignment]


def test_object_manager_get() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)

    assert manager.get('one') == 1
    assert manager.get('missing') is None


def test_object_manager_remove() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)
    manager.remove('one')

    assert 'one' not in manager


def test_object_manager_edit() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 2)
    manager.edit('one', 1)

    assert manager['one'] == 1


def test_object_manager_dunder_len() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)
    manager.add('two', 2)

    assert len(manager) == 2


def test_object_manager_mutable_mapping_iteration() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)
    manager.add('two', 2)

    assert isinstance(manager, MutableMapping)
    assert list(manager) == ['one', 'two']
    assert list(manager.values()) == [1, 2]
    assert dict(manager) == {'one': 1, 'two': 2}


def test_object_manager_dunder_getitem_raises_key_error() -> None:
    manager: ObjectManager[int] = ObjectManager()

    with pytest.raises(KeyError):
        _ = manager['one']


def test_object_manager_dunder_setitem() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager['one'] = 1

    assert manager['one'] == 1


def test_object_manager_dunder_delitem() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)
    del manager['one']

    assert 'one' not in manager


def test_object_manager_dunder_contains() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)

    assert 'one' in manager


def test_object_manager_keys_returns_keys() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)
    manager.add('two', 2)

    assert manager.keys() == {'one': 1, 'two': 2}.keys()
