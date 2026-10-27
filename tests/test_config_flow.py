import pytest
from unittest.mock import MagicMock
from custom_components.superfan_ir.config_flow import SuperfanConfigFlow, SuperfanOptionsFlow
from custom_components.superfan_ir.const import (
    CONF_BOOT_DELAY,
    CONF_EMITTER_ENTITY_ID,
    CONF_FAN_MODEL,
    CONF_IR_FORMAT,
    CONF_POWER_SWITCH,
    CONF_RECEIVER_ENTITY_ID,
    DEFAULT_BOOT_DELAY,
    IR_FORMAT_AUTO,
    IR_FORMAT_PRONTO,
    MODEL_ATOMBERG,
    MODEL_T10,
)


@pytest.mark.asyncio
async def test_config_flow_user_and_emitter_steps():
    flow = SuperfanConfigFlow()
    flow.hass = MagicMock()

    # Step 1: User Step
    res1 = await flow.async_step_user({
        "name": "Balcony Fan",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_AUTO,
    })
    assert res1["type"] == "form"
    assert res1["step_id"] == "emitter"

    # Step 2: Emitter Step
    res2 = await flow.async_step_emitter({CONF_EMITTER_ENTITY_ID: "infrared.blaster_2"})
    assert res2["type"] == "create_entry"
    assert res2["title"] == "Balcony Fan"
    assert res2["data"][CONF_EMITTER_ENTITY_ID] == "infrared.blaster_2"
    assert res2["data"][CONF_FAN_MODEL] == MODEL_ATOMBERG


@pytest.mark.asyncio
async def test_options_flow():
    entry = MagicMock()
    entry.data = {
        "name": "Balcony Fan",
        CONF_FAN_MODEL: MODEL_T10,
        CONF_IR_FORMAT: IR_FORMAT_AUTO,
        CONF_EMITTER_ENTITY_ID: "infrared.blaster_2",
    }
    entry.options = {}

    flow = SuperfanOptionsFlow(entry)
    flow.hass = MagicMock()

    form = await flow.async_step_init(None)
    assert form["type"] == "form"
    assert form["step_id"] == "init"

    res = await flow.async_step_init({
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_PRONTO,
        CONF_EMITTER_ENTITY_ID: "remote.broadlink_rm",
        CONF_RECEIVER_ENTITY_ID: "sensor.esphome_rx",
        CONF_POWER_SWITCH: "switch.smart_plug",
        CONF_BOOT_DELAY: 2.5,
    })
    assert res["type"] == "create_entry"
    assert res["data"][CONF_FAN_MODEL] == MODEL_ATOMBERG
    assert res["data"][CONF_IR_FORMAT] == IR_FORMAT_PRONTO
    assert res["data"][CONF_EMITTER_ENTITY_ID] == "remote.broadlink_rm"
    assert res["data"][CONF_RECEIVER_ENTITY_ID] == "sensor.esphome_rx"
    assert res["data"][CONF_POWER_SWITCH] == "switch.smart_plug"
    assert res["data"][CONF_BOOT_DELAY] == 2.5


@pytest.mark.asyncio
async def test_config_flow_tasmota_mqtt_topic():
    from custom_components.superfan_ir.const import CONF_MQTT_TOPIC, IR_FORMAT_TASMOTA

    flow = SuperfanConfigFlow()
    flow.hass = MagicMock()

    # Step 1: User chooses Tasmota format
    res1 = await flow.async_step_user({
        "name": "Tasmota Fan",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
    })
    assert res1["type"] == "form"
    assert res1["step_id"] == "emitter"

    # Step 2: Emitter Step with MQTT topic
    res2 = await flow.async_step_emitter({
        CONF_MQTT_TOPIC: "cmnd/tasmota_bedroom/IRsend",
    })
    assert res2["type"] == "create_entry"
    assert res2["data"][CONF_EMITTER_ENTITY_ID] == "cmnd/tasmota_bedroom/IRsend"


@pytest.mark.asyncio
async def test_config_flow_tasmota_remote_entity():
    from custom_components.superfan_ir.const import IR_FORMAT_TASMOTA

    flow = SuperfanConfigFlow()
    flow.hass = MagicMock()

    res1 = await flow.async_step_user({
        "name": "Tasmota Fan 2",
        CONF_FAN_MODEL: MODEL_T10,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
    })
    assert res1["step_id"] == "emitter"

    res2 = await flow.async_step_emitter({
        CONF_EMITTER_ENTITY_ID: "remote.living_blaster",
    })
    assert res2["type"] == "create_entry"
    assert res2["data"][CONF_EMITTER_ENTITY_ID] == "remote.living_blaster"


@pytest.mark.asyncio
async def test_config_flow_tasmota_missing_endpoint():
    from custom_components.superfan_ir.const import CONF_MQTT_TOPIC, IR_FORMAT_TASMOTA

    flow = SuperfanConfigFlow()
    flow.hass = MagicMock()

    await flow.async_step_user({
        "name": "Tasmota Fan 3",
        CONF_FAN_MODEL: MODEL_T10,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
    })

    res2 = await flow.async_step_emitter({
        CONF_MQTT_TOPIC: "",
        CONF_EMITTER_ENTITY_ID: None,
    })
    assert res2["type"] == "form"
    assert res2["errors"]["base"] == "missing_tasmota_endpoint"


@pytest.mark.asyncio
async def test_options_flow_tasmota():
    from custom_components.superfan_ir.const import CONF_MQTT_TOPIC, IR_FORMAT_TASMOTA

    entry = MagicMock()
    entry.data = {
        "name": "Tasmota Fan",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
        CONF_EMITTER_ENTITY_ID: "cmnd/tasmota_old/IRsend",
    }
    entry.options = {}

    flow = SuperfanOptionsFlow(entry)
    flow.hass = MagicMock()

    form = await flow.async_step_init(None)
    assert form["type"] == "form"

    res = await flow.async_step_init({
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
        CONF_MQTT_TOPIC: "cmnd/tasmota_new/IRsend",
    })
    assert res["type"] == "create_entry"
    assert res["data"][CONF_EMITTER_ENTITY_ID] == "cmnd/tasmota_new/IRsend"


@pytest.mark.asyncio
async def test_config_flow_tasmota_both_endpoints_rejected():
    from custom_components.superfan_ir.const import CONF_MQTT_TOPIC, IR_FORMAT_TASMOTA

    flow = SuperfanConfigFlow()
    flow.hass = MagicMock()

    await flow.async_step_user({
        "name": "Tasmota Dual",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
    })

    res = await flow.async_step_emitter({
        CONF_MQTT_TOPIC: "cmnd/tasmota/IRsend",
        CONF_EMITTER_ENTITY_ID: "remote.blaster",
    })
    assert res["type"] == "form"
    assert res["errors"]["base"] == "both_endpoints_provided"


@pytest.mark.asyncio
async def test_config_flow_tasmota_invalid_topic():
    from custom_components.superfan_ir.const import CONF_MQTT_TOPIC, IR_FORMAT_TASMOTA

    flow = SuperfanConfigFlow()
    flow.hass = MagicMock()

    await flow.async_step_user({
        "name": "Tasmota Invalid",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
    })

    # No slash
    res1 = await flow.async_step_emitter({CONF_MQTT_TOPIC: "invalidtopic"})
    assert res1["type"] == "form"
    assert res1["errors"]["base"] == "invalid_mqtt_topic"

    # Wildcard +
    res2 = await flow.async_step_emitter({CONF_MQTT_TOPIC: "cmnd/+/IRsend"})
    assert res2["type"] == "form"
    assert res2["errors"]["base"] == "invalid_mqtt_topic"


@pytest.mark.asyncio
async def test_options_flow_switch_format_single_submit():
    from custom_components.superfan_ir.const import CONF_MQTT_TOPIC, IR_FORMAT_TASMOTA

    entry = MagicMock()
    entry.data = {
        "name": "Switch Fan",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_AUTO,
        CONF_EMITTER_ENTITY_ID: "remote.old_blaster",
    }
    entry.options = {}

    flow = SuperfanOptionsFlow(entry)
    flow.hass = MagicMock()

    # Switch format from Auto to Tasmota in one single submit
    res = await flow.async_step_init({
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
        CONF_MQTT_TOPIC: "cmnd/switched_tasmota/IRsend",
        CONF_EMITTER_ENTITY_ID: None,
    })
    assert res["type"] == "create_entry"
    assert res["data"][CONF_EMITTER_ENTITY_ID] == "cmnd/switched_tasmota/IRsend"


@pytest.mark.asyncio
async def test_options_flow_non_tasmota_rejects_topic():
    from custom_components.superfan_ir.const import CONF_MQTT_TOPIC

    entry = MagicMock()
    entry.data = {
        "name": "Reject Topic Fan",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_AUTO,
        CONF_EMITTER_ENTITY_ID: "remote.old_blaster",
    }
    entry.options = {}

    flow = SuperfanOptionsFlow(entry)
    flow.hass = MagicMock()

    res = await flow.async_step_init({
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_AUTO,
        CONF_MQTT_TOPIC: "cmnd/unexpected/IRsend",
        CONF_EMITTER_ENTITY_ID: "remote.blaster",
    })
    assert res["type"] == "form"
    assert res["errors"]["base"] == "topic_not_supported_for_format"


@pytest.mark.asyncio
async def test_config_flow_tasmota_with_availability_topic():
    from custom_components.superfan_ir.const import (
        CONF_AVAILABILITY_TOPIC,
        CONF_MQTT_TOPIC,
        IR_FORMAT_TASMOTA,
    )

    flow = SuperfanConfigFlow()
    flow.hass = MagicMock()

    await flow.async_step_user({
        "name": "Tasmota Fan LWT",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
    })

    # Submit valid MQTT command and availability topics
    res = await flow.async_step_emitter({
        CONF_MQTT_TOPIC: "cmnd/tasmota_ir/IRsend",
        CONF_AVAILABILITY_TOPIC: "tele/tasmota_ir/LWT",
    })
    assert res["type"] == "create_entry"
    assert res["data"][CONF_EMITTER_ENTITY_ID] == "cmnd/tasmota_ir/IRsend"
    assert res["data"][CONF_AVAILABILITY_TOPIC] == "tele/tasmota_ir/LWT"


@pytest.mark.asyncio
async def test_config_flow_tasmota_invalid_availability_topic():
    from custom_components.superfan_ir.const import (
        CONF_AVAILABILITY_TOPIC,
        CONF_MQTT_TOPIC,
        IR_FORMAT_TASMOTA,
    )

    flow = SuperfanConfigFlow()
    flow.hass = MagicMock()

    await flow.async_step_user({
        "name": "Tasmota Fan Invalid LWT",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
    })

    # Wildcard in availability topic
    res = await flow.async_step_emitter({
        CONF_MQTT_TOPIC: "cmnd/tasmota_ir/IRsend",
        CONF_AVAILABILITY_TOPIC: "tele/+/LWT",
    })
    assert res["type"] == "form"
    assert res["errors"]["base"] == "invalid_availability_topic"


@pytest.mark.asyncio
async def test_options_flow_with_and_without_valid_availability_topic():
    from custom_components.superfan_ir.const import (
        CONF_AVAILABILITY_TOPIC,
        CONF_MQTT_TOPIC,
        IR_FORMAT_TASMOTA,
    )

    entry = MagicMock()
    entry.data = {
        "name": "Options LWT Fan",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
        CONF_EMITTER_ENTITY_ID: "cmnd/tasmota_ir/IRsend",
        CONF_AVAILABILITY_TOPIC: "tele/tasmota_ir/LWT",
    }
    entry.options = {}

    flow = SuperfanOptionsFlow(entry)
    flow.hass = MagicMock()

    # Invalid availability topic
    res_err = await flow.async_step_init({
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
        CONF_MQTT_TOPIC: "cmnd/tasmota_ir/IRsend",
        CONF_AVAILABILITY_TOPIC: "invalid_no_slash",
    })
    assert res_err["type"] == "form"
    assert res_err["errors"]["base"] == "invalid_availability_topic"

    # Valid updated availability topic
    res_ok = await flow.async_step_init({
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_TASMOTA,
        CONF_MQTT_TOPIC: "cmnd/tasmota_ir/IRsend",
        CONF_AVAILABILITY_TOPIC: "tele/new_topic/LWT",
    })
    assert res_ok["type"] == "create_entry"
    assert res_ok["data"][CONF_AVAILABILITY_TOPIC] == "tele/new_topic/LWT"


