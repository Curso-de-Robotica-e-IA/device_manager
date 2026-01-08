from device_manager.adb_executor import build_command_list


def test_manager_build_command_list():
    adb_cmd = r'shell am start -n dummyCmd\.dummyActv'
    result = build_command_list(
        base_command=['adb'],
        serial_number_list=['RXT8595', 'RXT8596'],
        custom_command=adb_cmd,
    )

    expected = [
        'adb',
        '-s',
        'RXT8595',
        'shell',
        'am',
        'start',
        '-n',
        r'dummyCmd\.dummyActv',
        '&&',
        'adb',
        '-s',
        'RXT8596',
        'shell',
        'am',
        'start',
        '-n',
        r'dummyCmd\.dummyActv',
    ]

    assert result == expected
