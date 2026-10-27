import logging
from typing import Any

from .const import (
    MODEL_ACTIVA,
    MODEL_ATOMBERG,
    MODEL_GOLDMEDAL,
    MODEL_ORIENT,
)

try:
    from infrared_protocols.commands import Command  # type: ignore[import-not-found, import-untyped]
except ImportError:
    class Command:  # type: ignore[no-redef]
        """Fallback Command class when infrared_protocols is not installed."""
        def __init__(self, modulation: int = 38000) -> None:
            self.modulation = modulation

_LOGGER = logging.getLogger(__name__)

class RawIRCommand(Command):  # type: ignore[misc, valid-type]
    """A raw IR command that takes a list of durations (in microseconds)."""
    
    def __init__(self, raw_timings: list[int], modulation: int = 38000) -> None:
        """Initialize the Raw IR command with alternating positive and negative durations."""
        super().__init__(modulation=modulation)
        self._raw_timings = []
        for i, t in enumerate(raw_timings):
            if i % 2 == 0:
                self._raw_timings.append(t)  # Pulse (high)
            else:
                self._raw_timings.append(-t) # Space (low)

    def get_raw_timings(self) -> list[int]:
        """Get raw timings for the command."""
        return self._raw_timings


def get_manufacturer(model: str) -> str:
    """Return the manufacturer / brand name for a given fan model."""
    if model == MODEL_ATOMBERG:
        return "Atomberg"
    if model == MODEL_ACTIVA:
        return "Activa Appliances"
    if model == MODEL_ORIENT:
        return "Orient Electric"
    if model == MODEL_GOLDMEDAL:
        return "Goldmedal Electricals"
    return "Versa Drives (Superfan)"


def is_esphome_2026_10_or_newer(hass: Any, entity_id: str | None) -> bool:
    """Check if the emitter entity is backed by ESPHome 2026.10+ firmware."""
    if not entity_id or hass is None:
        return False
    try:
        import re
        import logging
        from homeassistant.helpers import entity_registry as er, device_registry as dr

        ent_reg = er.async_get(hass) if hasattr(er, "async_get") else None
        dev_reg = dr.async_get(hass) if hasattr(dr, "async_get") else None
        if not ent_reg or not dev_reg:
            return False

        entry = ent_reg.async_get(entity_id) if hasattr(ent_reg, "async_get") else None
        if not entry or not getattr(entry, "device_id", None):
            return False
        if getattr(entry, "platform", None) != "esphome":
            return False

        device = dev_reg.async_get(entry.device_id) if hasattr(dev_reg, "async_get") else None
        if not device or not getattr(device, "sw_version", None):
            return False

        match = re.match(r"^(\d+)\.(\d+)", str(device.sw_version).strip())
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            return (year, month) >= (2026, 10)
    except Exception as err:
        logging.getLogger(__name__).debug("Could not determine ESPHome firmware version for %s: %s", entity_id, err)
    return False


def is_blaster_available_by_sensor(state_val: Any, entity_id: str | None) -> bool:
    """Determine if blaster is available based on an availability or status entity."""
    if state_val is None or not entity_id:
        return True
    s = str(getattr(state_val, "state", state_val)).lower()
    if s in ("unavailable", "unknown", "none", ""):
        return False
    # Standard availability (switch ON = available, device_tracker 'home' = available)
    return s in ("on", "home", "connected", "true", "1")


def is_mqtt_topic(value: str | None) -> bool:
    """Return True if value represents an MQTT topic rather than a Home Assistant entity ID."""
    if not value or not isinstance(value, str):
        return False
    # MQTT topics usually contain '/' (e.g. cmnd/tasmota/IRsend) or start with cmnd/
    if "/" in value or value.startswith("cmnd/") or value.startswith("stat/") or value.startswith("tele/"):
        return True
    # If it has no dot, it cannot be a Home Assistant entity_id (domain.object_id)
    if "." not in value:
        return True
    return False


def emitter_available(
    hass: Any,
    emitter_id: str | None,
    availability_entity_id: str | None = None,
    blaster_override: bool = True,
) -> bool:
    """Return True if the IR blaster emitter is online and available."""
    if not blaster_override:
        return False

    if availability_entity_id and hass:
        st = hass.states.get(availability_entity_id)
        if st is not None and not is_blaster_available_by_sensor(st.state, availability_entity_id):
            return False

    if not emitter_id:
        return False

    if is_mqtt_topic(emitter_id):
        # Verify MQTT publish service is registered if hass services are loaded
        if hass and hasattr(hass, "services") and hasattr(hass.services, "has_service"):
            if not hass.services.has_service("mqtt", "publish"):
                return False
        try:
            from homeassistant.components import mqtt
            if hasattr(mqtt, "is_connected") and not mqtt.is_connected(hass):
                return False
        except (ImportError, AttributeError):
            return False
        except Exception as err:
            _LOGGER.debug("Unexpected error checking MQTT connection state: %s", err)
        return True

    if "." not in emitter_id:
        return True

    if hass and hasattr(hass, "states") and hasattr(hass.states, "get"):
        st = hass.states.get(emitter_id)
        if st is None or str(st.state).lower() in ("unavailable", "unknown", ""):
            return False

    return True

