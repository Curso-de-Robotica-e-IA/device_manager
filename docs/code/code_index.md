# Device Manager Documentation
This is an automatic documentation of the code base. It includes all the classes, functions, and methods in the code base.

## DeviceManager Class
::: device_manager.manager.DeviceManager
    handler: python
    options:
        members:
            - connected_devices
            - connect_devices
            - disconnect_devices
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
            - get_properties
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
            - install_apk
            - turn_on_screen
            - unlock_screen
            - home_button
    show_root_heading: true

The `DeviceActions` class also has a property called `camera`, that is an instance of the `CameraActions` class. This class is used to perform actions related to the camera.

### CameraActions Class
::: device_manager.action_modules.camera_actions.CameraActions
    handler: python
    options:
        members:
            - open
            - open_video
            - close
            - take_picture
            - clear_pictures
            - pull_pictures
    show_root_heading: true