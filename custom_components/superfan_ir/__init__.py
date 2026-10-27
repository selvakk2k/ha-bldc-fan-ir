from __future__ import annotations

import logging
from typing import Any, Callable
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import CONF_AVAILABILITY_TOPIC, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["fan", "sensor", "binary_sensor"]


class SuperfanEntryData:
    """Shared runtime data for a fan config entry."""

    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry
        self.last_controlled_via: str = "IR Blaster"
        self.ir_blaster_available_override: bool = True
        self.availability_topic: str | None = entry.options.get(
            CONF_AVAILABILITY_TOPIC, entry.data.get(CONF_AVAILABILITY_TOPIC)
        )
        self.listeners: list[Callable[[], None]] = []

    def set_last_controlled_via(self, source: str) -> None:
        """Update last controlled source and notify listeners."""
        if self.last_controlled_via != source:
            self.last_controlled_via = source
            self._notify_listeners()

    def set_blaster_override(self, available: bool) -> None:
        """Update IR blaster override availability and notify listeners."""
        if self.ir_blaster_available_override != available:
            self.ir_blaster_available_override = available
            self._notify_listeners()

    def _notify_listeners(self) -> None:
        """Notify registered state listeners."""
        for listener in list(self.listeners):
            try:
                listener()
            except Exception as err:
                _LOGGER.debug("Error notifying listener: %s", err)

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a state listener."""
        self.listeners.append(listener)
        return lambda: self.listeners.remove(listener) if listener in self.listeners else None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Superfan IR from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    entry_data = SuperfanEntryData(entry)
    hass.data[DOMAIN][entry.entry_id] = entry_data

    avail_topic = entry_data.availability_topic
    if avail_topic:
        try:
            from homeassistant.components import mqtt

            @callback
            def _async_mqtt_lwt_message(msg: Any) -> None:
                raw_payload = getattr(msg, "payload", msg)
                payload = str(raw_payload).strip().lower()
                _LOGGER.debug("MQTT availability message on %s: %s", avail_topic, payload)
                if payload in ("online", "1", "true", "connected", "home", "on"):
                    entry_data.set_blaster_override(True)
                elif payload in ("offline", "0", "false", "disconnected", "not_home", "away", "off"):
                    entry_data.set_blaster_override(False)

            if hasattr(mqtt, "async_subscribe"):
                unsub = await mqtt.async_subscribe(hass, avail_topic, _async_mqtt_lwt_message)
                if unsub:
                    entry.async_on_unload(unsub)
        except Exception as err:
            _LOGGER.warning("Could not subscribe to MQTT availability topic %s: %s", avail_topic, err)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry on options update."""
    await hass.config_entries.async_reload(entry.entry_id)
