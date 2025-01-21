import pytest
from device_manager.components.manager import ObjectManager


@pytest.mark.parametrize(
    'key, value',
    [
        ('one', 1),
        ('two', 2),
        ('three', 3),
    ],
)
def test_object_manager_add(key, value):
    manager = ObjectManager()
    manager.add(key, value)

    assert manager[key] == value


def test_object_manager_key_not_string():
    manager = ObjectManager()
    with pytest.raises(TypeError):
        manager.add(1, 1)


def test_object_manager_add_holds_just_one_type():
    manager = ObjectManager()
    with pytest.raises(TypeError):
        manager.add('one', 1)
        manager.add('two', '2')


def test_object_manager_get():
    manager = ObjectManager()
    manager.add('one', 1)

    assert manager.get('one') == 1


def test_object_manager_remove():
    manager = ObjectManager()
    manager.add('one', 1)
    manager.remove('one')

    assert 'one' not in manager


def test_object_manager_edit():
    manager = ObjectManager()
    manager.add('one', 2)
    manager.edit('one', 1)

    assert manager['one'] == 1


def test_object_manager_dunder_len():
    manager = ObjectManager()
    manager.add('one', 1)
    manager.add('two', 2)

    assert len(manager) == 2


def test_object_manager_dunder_iter():
    manager = ObjectManager()
    manager.add('one', 1)
    manager.add('two', 2)

    assert list(manager) == [1, 2]


def test_object_manager_dunder_getitem():
    manager = ObjectManager()
    manager.add('one', 1)

    assert manager['one'] == 1


def test_object_manager_dunder_getitem_returns_none():
    manager = ObjectManager()

    assert manager['one'] is None


def test_object_manager_dunder_setitem():
    manager = ObjectManager()
    manager['one'] = 1

    assert manager['one'] == 1


def test_object_manager_dunder_delitem():
    manager = ObjectManager()
    manager.add('one', 1)
    del manager['one']

    assert 'one' not in manager


def test_object_manager_dunder_contains():
    manager = ObjectManager()
    manager.add('one', 1)

    assert 'one' in manager
