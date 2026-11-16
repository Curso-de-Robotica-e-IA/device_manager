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


def test_object_manager_add_holds_just_one_type() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)
    with pytest.raises(TypeError):
        manager.add('two', '2') # pyright: ignore[reportArgumentType]


def test_object_manager_get() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)

    assert manager.get('one') == 1


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

    assert len(manager) == 2  # noqa: PLR2004


def test_object_manager_dunder_iter() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)
    manager.add('two', 2)

    assert list(manager) == [1, 2]


def test_object_manager_dunder_getitem() -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('one', 1)

    assert manager['one'] == 1


def test_object_manager_dunder_getitem_returns_none() -> None:
    manager: ObjectManager[int] = ObjectManager()

    assert manager['one'] is None


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
