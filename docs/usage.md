# Usage
The library is composed of three main classes: `DeviceManager`, `DeviceInfo` and `DeviceActions`, and two connection classes: `AdbPairing` and `AdbConnectionDiscovery` were made available to ease the process of pairing and connecting to devices.

You can either use the individual classes, or only the `DeviceManager` class, which is a composition of the other classes.

## Using the DeviceManager Class
The `DeviceManager` class is the main class of the library. With this object alone, you can connect to devices and iterate over them as if you were using an iterable object. The particularity is that you can access the `DeviceInfo` and `DeviceActions` objects for each device as if you were accessing a dictionary, but you can iterate over them as if you were iterating over a list.

```python title='Basic Usage' linenums='1'
from device_manager import DeviceManager

manager = DeviceManager()  # (1)!

# Provided you have the serial numbers of the devices you want to connect,
# and they are already paired, you can just call:
manager.connect_devices(
    'serial_number_1',
    'serial_number_2',
    'serial_number_3',
)  # (2)!


# Now you can iterate over the connected devices
for device in manager:
    print(device)  # (2)!
    device_info = device.info  # (3)!
    device_actions = device.actions  # (4)!
    print(device.serial_number)  # (5)!
    # Here you can do whatever you want with the device_info 
    # and device_actions objects


# Additionally, you can get direct access of the `DeviceInfo`
# and `DeviceActions` tuple using the serial number.

device_info, device_action = manager['serial_number_1']  # (6)!

```

1.  Create a DeviceManager object
2.  The `device` is a `named tuple` called `DeviceObjects` that contains the device serial_number, and the associated `DeviceInfo` and `DeviceActions` objects.
3.  Access the `DeviceInfo` object for the device
4.  Access the `DeviceActions` object for the device
5.  Access the serial number of the device
6.  Get the `DeviceInfo` and `DeviceActions` objects for the device with the serial number `'serial_number_1'`

## Showing the Visible Devices in the Network
To show the devices that are visible in the network, you can either use the
`DeviceManager` object, or the `DeviceConnection` class.

=== "Device Manager"

    ```python title='Device Manager' linenums='1'
    from device_manager import DeviceManager

    manager = DeviceManager()

    network_devices = manager.connector.visible_devices()  # (1)!
    ```

    1.  This will return a list of `ServiceInfo` objects that contain the information of the devices visible in the network. A `ServiceInfo` object is a `dataclass` containing the `serial_number`, `ip` and `port` of the device.

=== "Device Connection"

    ```python title='Device Connection' linenums='1'
    from device_manager.connection import DeviceConnection

    connection = DeviceConnection()

    network_devices = connection.visible_devices()  # (1)!
    ```

    1.  This is exactly the same as the previous example, but using the `DeviceConnection` class directly, instead of the `DeviceManager` object.


## Pairing to a Device
To pair to a device, you can either use directly the `AdbPairing` class, or create an instance of it using the `DeviceManager` object. You can either start and stop the `BrowserServer` manually, or use a context manager function to make it automatically.

The process uses a `ServiceBrowser` and `Zeroconf` to find the devices in the network, and a `QRCode` to show the pairing code.

=== "AdbPairing Manually"

    ```python title='Directly using the AdbPairing class' linenums='1'
    from device_manager import AdbPairing


    pairing_server = AdbPairing()

    pairing_server.start()  # (1)!

    qrcode = pairing_server.qrcode_string  # (2)!
    # Show it in a window, or print it in the terminal

    success = pairing_server.pair_devices()  # (3)!

    pairing_server.stop_pair_listener()  # (4)!
    ```

    1.  Start the pairing server
    2.  Get the QRCode string content to build the QRCode image. This will be in the format `WIFI:T:ADB;S:{service_name};P:{password};;`.
    3.  This will pair the devices that are visible in the network. It will return `True` if the pairing was successful, and `False` otherwise.
    4.  Stop the pairing server

=== "AdbPairing Context Manager"

    ```python title='Using the AdbPairing class with a context manager' linenums='1'
    from device_manager import AdbPairing


    pair_server = AdbPairing()

    with pair_server.pair() as qrcode_string:
        # Show the QRCode in a window, or print it in the terminal
        print(qrcode_string)

    # (1)
    ```

    1.  The pairing process will be automatically started and stopped when the context manager is used. The `qrcode_string` will be available inside the context manager.

=== "Device Manager"

    ```python title='Using the DeviceManager object' linenums='1'
    from device_manager import DeviceManager


    manager = DeviceManager()
    manager.adb_pairing_instance()  # (1)!

    qrcode = manager.adb_pair.qrcode_string  # (2)!

    # The rest of the process is the same as the previous examples.
    ```

    1.  This will create an instance of the `AdbPairing` class and store it in the `DeviceManager` object, within the `adb_pair` attribute.
    2.  Get the QRCode string content to build the QRCode image. This will be in the format `WIFI:T:ADB;S:{service_name};P:{password};;`.


## Sending ADB Commands to the Devices
To send ADB commands to the devices, you can use the associated `DeviceActions` object, or the `DeviceManager` object to send the commands to a set of devices.
Continuing the example from the [Basic Usage Section](#using-the-devicemanager-class) you can send commands to the devices like this:

```python title='Using the DeviceManager object' linenums='29'

manager.execute_adb_command(
    'input keyevent 3',
)  # (1)!

manager.execute_adb_command(
    'input keyevent 26',
    comm_uris=['serial_number_1', 'serial_number_2'],
)  # (2)!
```

1.  This will send the command `input keyevent 3` to all connected devices.
2.  This will send the command `input keyevent 26` to the devices with the serial numbers `'serial_number_1'` and `'serial_number_2'`.
