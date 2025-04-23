# Connection Classes
Those classes are used to start a Service Browser to pair and connect to devices.
This documentation is automatically generated from the code base.

## AdbPairing Class
::: device_manager.connection.adb_pairing.AdbPairing
    handler: python
    options:
        members:
            - service_browser_started
            - browser
            - zeroconf_status
            - qrcode_string
            - qrcode
            - qrcode_image
            - update_qrcode
            - start
            - qrcode_prompt_show
            - qrcode_cv_window_show
            - has_device_to_pairing
            - pair_devices
            - stop_pair_listener
            - pair
    show_root_heading: true

## AdbConnectionDiscovery Class
::: device_manager.connection.adb_connection_discovery.AdbConnectionDiscovery
    handler: python
    options:
        members:
            - start
            - start_discovery_listener
            - service_browser_started
            - browser
            - zeroconf_status
            - online_devices
            - offline_devices
            - get_service_info_for
            - connection_status_for_device
            - stop_discovery_listener
    show_root_heading: true

## DeviceConnection Class
::: device_manager.connection.device_connection.DeviceConnection
    handler: python
    options:
        members:
            - check_pairing
            - select_devices_to_connect
            - prompt_device_connection
            - visible_devices
            - close
            - is_connected
            - check_connections
            - build_comm_uri
            - establish_first_connection
            - validate_connection
            - connect_all_devices
            - start_connection
            - stop_connection
            - disconnect
    show_root_heading: true