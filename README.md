# Device Manager library documentation
`Device Manager` is a python library made to ease the process of pairing, connecting and interacting with Android devices through Android Debug Bridge (ADB). It provides not only a set of methods to execute `adb` commands at the
associated devices, but also some facility classes to manage the connection, the pairing process and the device interactions.

## Extra Dependencies
To be able to execute adb commands, this library requires that your running system has the necessary `android-tools-adb` and SDK dependecies. You can get them at the official [Android Developers Page](https://developer.android.com/tools/releases/platform-tools).

The current version of the library requires the following versions, and the compatibility with other versions are not guaranteed:
- Android Debug Bridge version 1.0.41
- SDK Version 35.0.2

## Installation
This library is still being developed and is not available on PyPi yet. To install it, you can clone the repository and build it using `poetry`.

After cloning the repository, you will need [`poetry`](https://python-poetry.org/)
to install the dependencies and build the library.

In the root of the repository, run the following commands:

```bash
poetry install
```

or, if you want to serve the documentation locally:
```
poetry install --with doc
```


```bash
poetry build -f wheel
```

After that, you can install the library using the generated wheel file, usually located in the `dist` folder.

## Documentation
The full documentation of the library was made using `mkdocs`. Currently, you can
access the documentation by cloning the repository, installing the dependencies and running the following command:

```bash
mkdocs serve
```

This will start a local server with the documentation. You can access it by opening your browser and going to `http://localhost:8000`.