# Device Manager Documentation
This is an automatic documentation of the code base. It includes all the classes, functions, and methods in the code base.

## DeviceManager Class
::: device_manager.manager.DeviceManager
    handler: python
    options:
        members:
            - connected_devices
            - connect_devices
            - get_device_info
            - get_device_actions
            - build_command_list
            - execute_adb_command
            - adb_pairing_instance
    show_root_heading: true

## DeviceInfo Class
::: device_manager.device_info.DeviceInfo
    handler: python
    options:
        members:
            - serial_number
            - actual_activity
            - is_screen_on
            - is_device_locked
            - get_screen_gui_xml
    show_root_heading: true

## DeviceActions Class
::: device_manager.device_actions.DeviceActions
    handler: python
    options:
        members:
            - serial_number
            - click_by_coordinates
            - swipe
            - open_app
            - close_app
            - turn_on_screen
            - unlock_screen
            - home_button
    show_root_heading: true