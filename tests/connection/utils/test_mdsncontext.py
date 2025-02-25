import pytest

from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.service_info import ServiceInfo


@pytest.fixture
def sample_service_info():
    return ServiceInfo(
        serial_number='abc123xyz',
        ip='111.000.101.01',
        port=8000,
    )


@pytest.fixture
def empty_mdns_context():
    return MDnsContext()


@pytest.fixture
def mdns_context_with_services(sample_service_info):
    s2 = ServiceInfo(
        serial_number='def456uvw',
        ip='111.000.101.01',
        port=8002,
    )
    s3 = ServiceInfo(
        serial_number='ghi789rst',
        ip='111.000.101.01',
        port=8003,
    )
    context = MDnsContext()
    context.add_service(sample_service_info.serial_number, sample_service_info)
    context.add_service(s2.serial_number, s2)
    context.add_service(s3.serial_number, s3)
    return context


def test_mdns_context_add_service(empty_mdns_context, sample_service_info):
    empty_mdns_context.add_service(
        sample_service_info.serial_number,
        sample_service_info,
    )
    online_list = empty_mdns_context.get_online_service()
    assert sample_service_info.serial_number in online_list.keys()


def test_mdns_context_add_multiple_services(
    empty_mdns_context,
    sample_service_info,
):
    second_service = ServiceInfo(
        serial_number='def456uvw',
        ip='000.111.010.10',
        port=8001,
    )
    empty_mdns_context.add_service(
        sample_service_info.serial_number,
        sample_service_info,
    )
    empty_mdns_context.add_service(
        second_service.serial_number,
        second_service,
    )
    online_list = empty_mdns_context.get_online_service()

    assert sample_service_info.serial_number in online_list.keys()
    assert second_service.serial_number in online_list.keys()


def test_mdns_context_update_service(
    mdns_context_with_services,
    sample_service_info,
):
    NEW_PORT = 5555
    sample_service_info.port = NEW_PORT
    mdns_context_with_services.update_service(
        sample_service_info.serial_number,
        sample_service_info,
    )

    online_list = mdns_context_with_services.get_online_service()
    assert online_list[sample_service_info.serial_number].port == NEW_PORT


def test_mdns_context_to_offline_service(
    mdns_context_with_services,
    sample_service_info,
):
    mdns_context_with_services.to_offline_service(
        sample_service_info.serial_number,
        sample_service_info,
    )

    online_list = mdns_context_with_services.get_online_service()
    offline_list = mdns_context_with_services.get_offline_service()

    assert sample_service_info.serial_number not in online_list.keys()
    assert sample_service_info.serial_number in offline_list.keys()


def test_adding_service_already_in_offline_list(
    mdns_context_with_services,
    sample_service_info,
):
    mdns_context_with_services.to_offline_service(
        sample_service_info.serial_number,
        sample_service_info,
    )

    mdns_context_with_services.add_service(
        sample_service_info.serial_number,
        sample_service_info,
    )

    online_list = mdns_context_with_services.get_online_service()
    offline_list = mdns_context_with_services.get_offline_service()

    assert sample_service_info.serial_number in online_list.keys()
    assert sample_service_info.serial_number not in offline_list.keys()


def test_updating_service_from_offline_list(
    mdns_context_with_services,
    sample_service_info,
):
    mdns_context_with_services.to_offline_service(
        sample_service_info.serial_number,
        sample_service_info,
    )

    sample_service_info.port = 5555
    mdns_context_with_services.update_service(
        sample_service_info.serial_number,
        sample_service_info,
    )

    online_list = mdns_context_with_services.get_online_service()
    offline_list = mdns_context_with_services.get_offline_service()

    assert sample_service_info.serial_number in online_list.keys()
    assert sample_service_info.serial_number not in offline_list.keys()


def test_online_service_list_property(mdns_context_with_services):
    online_list = mdns_context_with_services.online_service_list
    expected_length = 3
    assert len(online_list) == expected_length
    assert isinstance(online_list[0], ServiceInfo)


def test_offline_service_list_property(
    mdns_context_with_services,
    sample_service_info,
):
    mdns_context_with_services.to_offline_service(
        sample_service_info.serial_number,
        sample_service_info,
    )
    offline_list = mdns_context_with_services.offline_service_list
    assert len(offline_list) == 1
    assert isinstance(offline_list[0], ServiceInfo)
