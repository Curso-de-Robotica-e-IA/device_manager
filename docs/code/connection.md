# Connection Classes

Classes responsible for USB scanning, mDNS/Zeroconf discovery, pairing, and ADB connection lifecycle.

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
            - set_password
            - start
            - has_device_to_pairing
            - pair_devices
            - pair_device_with_paring_code
            - stop_pair_listener
            - pair
    show_root_heading: true

## AsyncAdbPairing Class
::: device_manager.asyncio_dm.async_adb_pairing.AsyncAdbPairing
    handler: python
    options:
        members:
            - service_browser_started
            - browser
            - zeroconf_status
            - qrcode_string
            - qrcode
            - qrcode_image
            - start
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
            - visible_devices
            - list_adb_device_states
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
