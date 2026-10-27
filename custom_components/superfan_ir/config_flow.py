"""Config flow and Options flow for Indian BLDC IR Fan integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AVAILABILITY_ENTITY_ID,
    CONF_BOOT_DELAY,
    CONF_EMITTER_ENTITY_ID,
    CONF_FAN_MODEL,
    CONF_IR_FORMAT,
    CONF_MQTT_TOPIC,
    CONF_POWER_SWITCH,
    CONF_RECEIVER_ENTITY_ID,
    DEFAULT_BOOT_DELAY,
    DEFAULT_TASMOTA_TOPIC,
    DOMAIN,
    IR_FORMAT_AUTO,
    IR_FORMAT_OPTIONS,
    IR_FORMAT_TASMOTA,
    MODEL_ATOMBERG,
    MODEL_OPTIONS,
)
from .utils import is_mqtt_topic


def _get_model_select_options() -> list[selector.SelectOptionDict]:
    return [
        selector.SelectOptionDict(
            value=key,
            label=label,
        )
        for key, label in MODEL_OPTIONS.items()
    ]


def _get_ir_format_select_options() -> list[selector.SelectOptionDict]:
    return [
        selector.SelectOptionDict(
            value=key,
            label=label,
        )
        for key, label in IR_FORMAT_OPTIONS.items()
    ]


def validate_mqtt_topic(topic: str | None) -> bool:
    """Validate MQTT topic: must not be empty, must contain '/', no wildcards '#' or '+'."""
    if not topic or not isinstance(topic, str):
        return False
    t = topic.strip()
    if not t or "/" not in t:
        return False
    if "#" in t or "+" in t:
        return False
    return True


class SuperfanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Indian BLDC fan IR integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_emitter()

        data_schema = vol.Schema({
            vol.Required("name", default="Living Room Fan"): selector.TextSelector(),
            vol.Required(CONF_FAN_MODEL, default=MODEL_ATOMBERG): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_get_model_select_options(),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_IR_FORMAT, default=IR_FORMAT_AUTO): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_get_ir_format_select_options(),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_emitter(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle selecting transmitter entity or MQTT topic."""
        errors: dict[str, str] = {}
        ir_fmt = self.data.get(CONF_IR_FORMAT, IR_FORMAT_AUTO)

        if user_input is not None:
            clean_input = dict(user_input)
            if ir_fmt == IR_FORMAT_TASMOTA:
                mqtt_topic = (user_input.get(CONF_MQTT_TOPIC) or "").strip()
                remote_entity = user_input.get(CONF_EMITTER_ENTITY_ID)
                if mqtt_topic and remote_entity:
                    errors["base"] = "both_endpoints_provided"
                elif not mqtt_topic and not remote_entity:
                    errors["base"] = "missing_tasmota_endpoint"
                elif mqtt_topic and not validate_mqtt_topic(mqtt_topic):
                    errors["base"] = "invalid_mqtt_topic"
                else:
                    clean_input[CONF_EMITTER_ENTITY_ID] = mqtt_topic if mqtt_topic else remote_entity
                    self.data.update(clean_input)
                    return self.async_create_entry(title=self.data["name"], data=self.data)
            else:
                remote_entity = user_input.get(CONF_EMITTER_ENTITY_ID)
                if not remote_entity or is_mqtt_topic(remote_entity):
                    errors["base"] = "invalid_emitter_entity"
                else:
                    self.data.update(clean_input)
                    return self.async_create_entry(title=self.data["name"], data=self.data)

        if ir_fmt == IR_FORMAT_TASMOTA:
            data_schema = vol.Schema({
                vol.Optional(CONF_MQTT_TOPIC): selector.TextSelector(),
                vol.Optional(CONF_EMITTER_ENTITY_ID): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="remote")
                ),
                vol.Optional(CONF_AVAILABILITY_ENTITY_ID): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["binary_sensor", "input_boolean", "switch", "device_tracker"])
                ),
            })
            if hasattr(self, "add_suggested_values_to_schema"):
                data_schema = self.add_suggested_values_to_schema(
                    data_schema, {CONF_MQTT_TOPIC: DEFAULT_TASMOTA_TOPIC}
                )
        else:
            if ir_fmt in ("raw", "auto"):
                emitter_selector = selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["infrared", "remote"])
                )
            else:
                emitter_selector = selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="remote")
                )

            data_schema = vol.Schema({
                vol.Required(CONF_EMITTER_ENTITY_ID): emitter_selector,
                vol.Optional(CONF_AVAILABILITY_ENTITY_ID): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["binary_sensor", "input_boolean", "switch", "device_tracker"])
                ),
            })

        return self.async_show_form(
            step_id="emitter",
            data_schema=data_schema,
            description_placeholders={"name": self.data.get("name", "Fan")},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return SuperfanOptionsFlow(config_entry)


class SuperfanOptionsFlow(OptionsFlow):
    """Handle options for Indian BLDC fans."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            clean_input = dict(user_input)
            fmt = clean_input.get(CONF_IR_FORMAT)
            mqtt_topic = (clean_input.get(CONF_MQTT_TOPIC) or "").strip()
            remote_ent = clean_input.get(CONF_EMITTER_ENTITY_ID)

            if fmt == IR_FORMAT_TASMOTA:
                if mqtt_topic and remote_ent:
                    errors["base"] = "both_endpoints_provided"
                elif not mqtt_topic and not remote_ent:
                    errors["base"] = "missing_tasmota_endpoint"
                elif mqtt_topic and not validate_mqtt_topic(mqtt_topic):
                    errors["base"] = "invalid_mqtt_topic"
                else:
                    clean_input[CONF_EMITTER_ENTITY_ID] = mqtt_topic if mqtt_topic else remote_ent
                    return self.async_create_entry(title="", data=clean_input)
            else:
                if mqtt_topic:
                    errors["base"] = "topic_not_supported_for_format"
                elif not remote_ent or is_mqtt_topic(remote_ent):
                    errors["base"] = "invalid_emitter_entity"
                else:
                    clean_input[CONF_EMITTER_ENTITY_ID] = remote_ent
                    clean_input[CONF_MQTT_TOPIC] = ""
                    return self.async_create_entry(title="", data=clean_input)

        current_model = self._config_entry.options.get(
            CONF_FAN_MODEL,
            self._config_entry.data.get(CONF_FAN_MODEL, MODEL_ATOMBERG),
        )
        current_fmt = self._config_entry.options.get(
            CONF_IR_FORMAT,
            self._config_entry.data.get(CONF_IR_FORMAT, IR_FORMAT_AUTO),
        )
        current_emitter = self._config_entry.options.get(
            CONF_EMITTER_ENTITY_ID,
            self._config_entry.data.get(CONF_EMITTER_ENTITY_ID),
        )
        current_topic = self._config_entry.options.get(
            CONF_MQTT_TOPIC,
            self._config_entry.data.get(CONF_MQTT_TOPIC),
        )
        if not current_topic and is_mqtt_topic(current_emitter):
            current_topic = current_emitter

        current_receiver = self._config_entry.options.get(
            CONF_RECEIVER_ENTITY_ID,
            self._config_entry.data.get(CONF_RECEIVER_ENTITY_ID, ""),
        )
        current_switch = self._config_entry.options.get(
            CONF_POWER_SWITCH,
            self._config_entry.data.get(CONF_POWER_SWITCH, ""),
        )
        current_avail = self._config_entry.options.get(
            CONF_AVAILABILITY_ENTITY_ID,
            self._config_entry.data.get(CONF_AVAILABILITY_ENTITY_ID, ""),
        )
        current_boot_delay = float(
            self._config_entry.options.get(
                CONF_BOOT_DELAY,
                self._config_entry.data.get(CONF_BOOT_DELAY, DEFAULT_BOOT_DELAY),
            )
        )

        schema_dict: dict[Any, Any] = {
            vol.Required(CONF_FAN_MODEL): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_get_model_select_options(),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_IR_FORMAT): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_get_ir_format_select_options(),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_EMITTER_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["infrared", "remote"])
            ),
            vol.Optional(CONF_MQTT_TOPIC): selector.TextSelector(),
            vol.Optional(CONF_RECEIVER_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["infrared", "remote"])
            ),
            vol.Optional(CONF_AVAILABILITY_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["binary_sensor", "input_boolean", "switch", "device_tracker"])
            ),
            vol.Optional(CONF_POWER_SWITCH): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="switch")
            ),
            vol.Optional(CONF_BOOT_DELAY, default=DEFAULT_BOOT_DELAY): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.5,
                    max=5.0,
                    step=0.1,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
        }

        schema = vol.Schema(schema_dict)

        suggested = {
            CONF_FAN_MODEL: current_model,
            CONF_IR_FORMAT: current_fmt,
            CONF_MQTT_TOPIC: current_topic if is_mqtt_topic(current_emitter) else None,
            CONF_EMITTER_ENTITY_ID: current_emitter if not is_mqtt_topic(current_emitter) else None,
            CONF_RECEIVER_ENTITY_ID: current_receiver,
            CONF_AVAILABILITY_ENTITY_ID: current_avail,
            CONF_POWER_SWITCH: current_switch,
            CONF_BOOT_DELAY: current_boot_delay,
        }
        schema = self.add_suggested_values_to_schema(schema, suggested)

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
