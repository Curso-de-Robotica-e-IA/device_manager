from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_subprocess_run(monkeypatch):
    """
    Base fixture to mock subprocess.run calls.
    """

    def _mock_impl(stdout_content, returncode=0):
        mock_result = MagicMock()
        mock_result.stdout = stdout_content
        mock_result.returncode = returncode

        monkeypatch.setattr(
            'subprocess.run', lambda *args, **kwargs: mock_result
        )
        return mock_result

    return _mock_impl


@pytest.fixture
def mock_two_devices_unauthorized(mock_subprocess_run):
    """Tow devices listed, both unauthorized."""
    output = (
        'List of devices attached\n'
        'RXT8595\tunauthorized\n'
        'RXT8596\tunauthorized\n'
    )
    return mock_subprocess_run(output)


@pytest.fixture
def mock_two_devices_authorized(mock_subprocess_run):
    """Two devices listed, both connected and ready."""
    output = 'List of devices attached\nRXT8595\tdevice\nRXT8596\tdevice\n'
    return mock_subprocess_run(output)


@pytest.fixture
def mock_mixed_devices(mock_subprocess_run):
    """Scenario: One authorized and one unauthorized."""
    output = (
        'List of devices attached\n'
        'RXT8595\tdevice\n'
        'RXT8596\tunauthorized\n'
        'RXT8597\toffline\n'
    )
    return mock_subprocess_run(output)
