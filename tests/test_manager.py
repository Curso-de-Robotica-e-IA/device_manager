from device_manager.adb_executor import build_command_list


def test_manager_build_command_list():
    adb_cmd = r'shell am start -n dummyCmd\.dummyActv'
    result = build_command_list(
        base_command=['adb'],
        comm_uri_list=['127.0.0.1:5555', '127.0.0.2:5555'],
        custom_command=adb_cmd,
    )

    expected = [
        'adb',
        '-s',
        '127.0.0.1:5555',
        'shell',
        'am',
        'start',
        '-n',
        r'dummyCmd\.dummyActv',
        '&&',
        'adb',
        '-s',
        '127.0.0.2:5555',
        'shell',
        'am',
        'start',
        '-n',
        r'dummyCmd\.dummyActv',
    ]

    assert result == expected
