# Base Classes

Automatic API documentation generated from the `device_manager` codebase.

## DeviceManager Class
::: device_manager.manager.DeviceManager
    handler: python
    options:
        members:
            - connected_devices
            - available_devices
            - unauthorized_devices
            - visible_devices
            - connect_devices
            - disconnect_devices
            - load_connected_usb_devices
            - get_device_info
            - get_device_actions
            - is_connected
            - execute_adb_command
            - adb_pairing_instance
            - clear
            - close
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
            - get_screen_state
            - get_screen_gui_xml
            - get_properties
            - get_screen_dimensions
            - get_display_orientation
            - get_device_model
            - list_installed_all_apps
            - is_app_installed
            - is_app_running
            - get_app_path
            - get_all_touchscreens
            - get_touchscreen_events
            - get_touchscreen_info
            - get_touch_axis_ranges
    show_root_heading: true

## DeviceActions Class
::: device_manager.device_actions.DeviceActions
    handler: python
    options:
        members:
            - serial_number
            - click_by_coordinates
            - click_by_text
            - swipe
            - open_app
            - start_app
            - close_app
            - install_apk
            - uninstall_apk
            - turn_on_screen
            - wake_up_screen
            - unlock_screen
            - keep_screen_on_and_awake
            - home_button
            - back
            - screen_shot
            - safe_screencap_bytes
            - take_screenshot_to_file
            - push_file
            - pull_file
            - remove_file
            - set_android_setting
            - start_stream
    show_root_heading: true

### CameraActions Class (`actions.camera`)
::: device_manager.actions.camera_actions.CameraActions
    handler: python
    options:
        members:
            - open
            - open_video
            - close
            - package
            - take_picture
            - clear_pictures
            - pull_pictures
            - pull_picture_by_name
    show_root_heading: true

## Resident UI & Screenshot Backend
::: device_manager.ui_hierarchy.NativeResidentUiBackend
    handler: python
    options:
        members:
            - dump_xml
            - take_screenshot
            - save_screenshot
            - close
    show_root_heading: true

## ADB Streaming (`adbutils`)
::: device_manager.adb_stream.AdbStreamProcess
    handler: python
    options:
        members:
            - command
            - is_open
            - iter_lines
            - read_chunks
            - close
            - terminate
    show_root_heading: true
