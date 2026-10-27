"""Binary sensor platform for Indian BLDC Fan integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_AVAILABILITY_ENTITY_ID,
    CONF_AVAILABILITY_TOPIC,
    CONF_EMITTER_ENTITY_ID,
    CONF_FAN_MODEL,
    DOMAIN,
    MODEL_ATOMBERG,
)
from .utils import (
    emitter_available,
    get_manufacturer,
    is_blaster_available_by_sensor,
    is_mqtt_topic,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    emitter_id = entry.options.get(
        CONF_EMITTER_ENTITY_ID, entry.data.get(CONF_EMITTER_ENTITY_ID)
    )
    availability_id = entry.options.get(
        CONF_AVAILABILITY_ENTITY_ID, entry.data.get(CONF_AVAILABILITY_ENTITY_ID)
    )
    availability_topic = entry.options.get(
        CONF_AVAILABILITY_TOPIC, entry.data.get(CONF_AVAILABILITY_TOPIC)
    )
    fan_model = entry.options.get(
        CONF_FAN_MODEL, entry.data.get(CONF_FAN_MODEL, MODEL_ATOMBERG)
    )

    async_add_entities([
        SuperfanIRBlasterAvailableBinarySensor(
            entry=entry,
            fan_model=fan_model,
            emitter_id=emitter_id,
            availability_entity_id=availability_id,
            availability_topic=availability_topic,
        )
    ])


class SuperfanIRBlasterAvailableBinarySensor(BinarySensorEntity):
    """Binary sensor reporting connectivity/availability of the configured IR transmitter."""

    _attr_has_entity_name = True
    _attr_translation_key = "ir_blaster_available"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        fan_model: str,
        emitter_id: str | None,
        availability_entity_id: str | None = None,
        availability_topic: str | None = None,
    ) -> None:
        """Initialize binary sensor."""
        self._entry = entry
        self._model = fan_model
        self._emitter_id = emitter_id
        self._availability_entity_id = availability_entity_id
        self._availability_topic = availability_topic
        self._attr_unique_id = f"{entry.entry_id}_ir_blaster_available"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": get_manufacturer(fan_model),
            "model": fan_model,
        }

    @property
    def is_on(self) -> bool:
        """Return true if the IR blaster is online and available."""
        entry_data = None
        if hasattr(self, "hass") and self.hass:
            entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        blaster_override = entry_data.ir_blaster_available_override if entry_data else True
        return emitter_available(
            self.hass if hasattr(self, "hass") else None,
            self._emitter_id,
            self._availability_entity_id,
            blaster_override=blaster_override,
        )

    async def async_added_to_hass(self) -> None:
        """Register state change listeners."""
        if hasattr(super(), "async_added_to_hass"):
            await super().async_added_to_hass()
        if hasattr(self, "hass") and self.hass:
            entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
            if entry_data and hasattr(entry_data, "add_listener"):
                self.async_on_remove(entry_data.add_listener(self.async_write_ha_state))

        if self._emitter_id:
            if is_mqtt_topic(self._emitter_id):
                try:
                    from homeassistant.components.mqtt.const import MQTT_CONNECTION_STATE
                except ImportError:
                    MQTT_CONNECTION_STATE = "mqtt_connection_state"
                from homeassistant.helpers.dispatcher import async_dispatcher_connect

                self.async_on_remove(
                    async_dispatcher_connect(
                        self.hass,
                        MQTT_CONNECTION_STATE,
                        self._async_mqtt_connection_changed,
                    )
                )
            elif "." in self._emitter_id:
                self.async_on_remove(
                    async_track_state_change_event(
                        self.hass, [self._emitter_id], self._async_emitter_changed
                    )
                )
        if self._availability_entity_id and "." in self._availability_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._availability_entity_id], self._async_emitter_changed
                )
            )

    @callback
    def _async_emitter_changed(self, event: Event) -> None:
        """Handle blaster state change."""
        self.async_write_ha_state()

    @callback
    def _async_mqtt_connection_changed(self, status: bool | None = None) -> None:
        """Handle MQTT broker connection state updates."""
        self.async_write_ha_state()
