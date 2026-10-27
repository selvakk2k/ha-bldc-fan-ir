import pytest
from unittest.mock import MagicMock
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from custom_components.superfan_ir.binary_sensor import SuperfanIRBlasterAvailableBinarySensor
from custom_components.superfan_ir.sensor import SuperfanLastControlledViaSensor
from custom_components.superfan_ir.const import MODEL_ATOMBERG, DOMAIN
from custom_components.superfan_ir import SuperfanEntryData


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.title = "Living Room Fan"
    entry.data = {"name": "Living Room Fan", "fan_model": MODEL_ATOMBERG, "emitter_entity_id": "infrared.blaster"}
    entry.options = {}
    return entry


@pytest.mark.asyncio
async def test_ir_blaster_available_binary_sensor(mock_entry):
    sensor = SuperfanIRBlasterAvailableBinarySensor(
        entry=mock_entry,
        fan_model=MODEL_ATOMBERG,
        emitter_id="infrared.blaster",
    )
    sensor.hass = MagicMock()
    
    # Blaster state is online
    blaster_state = MagicMock(state="idle")
    sensor.hass.states.get.return_value = blaster_state
    assert sensor.is_on is True

    # Blaster state is unavailable
    blaster_state.state = "unavailable"
    assert sensor.is_on is False

    # Blaster is ESPHome raw string (no dot)
    sensor._emitter_id = "ir_blaster"
    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_last_controlled_via_sensor(mock_entry):
    sensor = SuperfanLastControlledViaSensor(
        entry=mock_entry,
        fan_model=MODEL_ATOMBERG,
    )
    sensor.hass = MagicMock()
    entry_data = SuperfanEntryData(mock_entry)
    sensor.hass.data = {DOMAIN: {mock_entry.entry_id: entry_data}}

    assert sensor.native_value == "IR Blaster"
    assert sensor.icon == "mdi:home-assistant"

    # Change to Physical IR Remote
    entry_data.set_last_controlled_via("IR Remote")
    assert sensor.native_value == "IR Remote"
    assert sensor.icon == "mdi:remote"

    # Change to Mains Switch
    entry_data.set_last_controlled_via("Mains Switch")
    assert sensor.native_value == "Mains Switch"
    assert sensor.icon == "mdi:toggle-switch"


def test_device_info_manufacturer_resolution(mock_entry):
    """Verify that get_manufacturer correctly assigns manufacturers across platforms."""
    from custom_components.superfan_ir.const import (
        MODEL_ACTIVA,
        MODEL_ATOMBERG,
        MODEL_GOLDMEDAL,
        MODEL_ORIENT,
        MODEL_T10,
        MODEL_T12_6,
    )
    from custom_components.superfan_ir.utils import get_manufacturer

    assert get_manufacturer(MODEL_ATOMBERG) == "Atomberg"
    assert get_manufacturer(MODEL_ACTIVA) == "Activa Appliances"
    assert get_manufacturer(MODEL_ORIENT) == "Orient Electric"
    assert get_manufacturer(MODEL_GOLDMEDAL) == "Goldmedal Electricals"
    assert get_manufacturer(MODEL_T10) == "Versa Drives (Superfan)"
    assert get_manufacturer(MODEL_T12_6) == "Versa Drives (Superfan)"

    # Verify sensor device_info uses get_manufacturer
    sensor = SuperfanLastControlledViaSensor(mock_entry, MODEL_ORIENT)
    assert sensor._attr_device_info["manufacturer"] == "Orient Electric"

    # Verify binary sensor device_info uses get_manufacturer
    binary_sensor = SuperfanIRBlasterAvailableBinarySensor(mock_entry, MODEL_GOLDMEDAL, "remote.blaster")
    assert binary_sensor._attr_device_info["manufacturer"] == "Goldmedal Electricals"


@pytest.mark.asyncio
async def test_binary_sensor_reflects_shared_override(mock_entry):
    sensor = SuperfanIRBlasterAvailableBinarySensor(
        entry=mock_entry,
        fan_model=MODEL_ATOMBERG,
        emitter_id="infrared.blaster",
    )
    sensor.hass = MagicMock()
    entry_data = SuperfanEntryData(mock_entry)
    sensor.hass.data = {DOMAIN: {mock_entry.entry_id: entry_data}}

    blaster_state = MagicMock(state="idle")
    sensor.hass.states.get.return_value = blaster_state
    assert sensor.is_on is True

    # When override is set to False (e.g. ESPHome timeout), binary sensor turns False
    entry_data.set_blaster_override(False)
    assert sensor.is_on is False

    # When override is restored to True, binary sensor turns True
    entry_data.set_blaster_override(True)
    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_binary_sensor_mqtt_topic_dispatcher(mock_entry):
    """Test that binary sensor registers MQTT_CONNECTION_STATE dispatcher for topics."""
    from unittest.mock import patch

    sensor = SuperfanIRBlasterAvailableBinarySensor(
        entry=mock_entry,
        fan_model=MODEL_ATOMBERG,
        emitter_id="cmnd/tasmota_fan_ir/IRsend",
    )
    sensor.hass = MagicMock()
    sensor.hass.data = {DOMAIN: {mock_entry.entry_id: SuperfanEntryData(mock_entry)}}

    with patch("homeassistant.helpers.dispatcher.async_dispatcher_connect") as mock_dispatch:
        await sensor.async_added_to_hass()
        mock_dispatch.assert_called_once()
        signal_arg = mock_dispatch.call_args[0][1]
        assert signal_arg == "mqtt_connection_state"
        callback_arg = mock_dispatch.call_args[0][2]

        with patch.object(sensor, "async_write_ha_state") as mock_write:
            callback_arg(False)
            mock_write.assert_called_once()


@pytest.mark.asyncio
async def test_binary_sensor_with_availability_topic(mock_entry):
    """Test that binary sensor tracks availability when using an availability topic."""
    from custom_components.superfan_ir.const import CONF_AVAILABILITY_TOPIC

    mock_entry.data[CONF_AVAILABILITY_TOPIC] = "tele/tasmota_ir/LWT"
    entry_data = SuperfanEntryData(mock_entry)
    sensor = SuperfanIRBlasterAvailableBinarySensor(
        entry=mock_entry,
        fan_model=MODEL_ATOMBERG,
        emitter_id="cmnd/tasmota_fan_ir/IRsend",
        availability_topic="tele/tasmota_ir/LWT",
    )
    sensor.hass = MagicMock()
    sensor.hass.data = {DOMAIN: {mock_entry.entry_id: entry_data}}

    assert sensor.is_on is True

    # Offline LWT message sets override to False
    entry_data.set_blaster_override(False)
    assert sensor.is_on is False

    # Online LWT message restores to True
    entry_data.set_blaster_override(True)
    assert sensor.is_on is True

