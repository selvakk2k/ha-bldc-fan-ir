import sys
from pathlib import Path
from enum import IntFlag

# Set up Home Assistant mock stubs for standalone testing
from tests.ha_stub import setup_ha_stubs
setup_ha_stubs()

class FanEntityFeature(IntFlag):
    SET_SPEED = 1
    OSCILLATE = 2
    DIRECTION = 4
    PRESET_MODE = 8
    TURN_OFF = 16
    TURN_ON = 32

import homeassistant.core
class Event:
    def __init__(self, event_type="", data=None, **kwargs):
        self.event_type = event_type
        self.data = data or {}
homeassistant.core.Event = Event

import homeassistant.helpers.entity
class Entity:
    _attr_name = None
    _context = None
    _attr_unique_id = None
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_assumed_state = False

    @property
    def name(self):
        return self._attr_name

    def __init__(self, *args, **kwargs):
        self._context = None

    def async_write_ha_state(self):
        pass

    def async_on_remove(self, func):
        pass

    async def async_added_to_hass(self):
        pass

homeassistant.helpers.entity.Entity = Entity

import homeassistant.components.binary_sensor
class BinarySensorEntity(Entity):
    pass
homeassistant.components.binary_sensor.BinarySensorEntity = BinarySensorEntity

import homeassistant.components.sensor
class SensorEntity(Entity):
    pass
homeassistant.components.sensor.SensorEntity = SensorEntity

import homeassistant.components.fan
homeassistant.components.fan.FanEntityFeature = FanEntityFeature

class FanEntity(Entity):
    _attr_is_on = None
    _attr_percentage = None
    _attr_speed_count = 100
    _attr_preset_mode = None
    _attr_preset_modes = None

    @property
    def is_on(self) -> bool | None:
        return self._attr_is_on

    @property
    def percentage(self) -> int | None:
        return self._attr_percentage

    @property
    def speed_count(self) -> int:
        return self._attr_speed_count

    @property
    def preset_mode(self) -> str | None:
        return self._attr_preset_mode

    @property
    def preset_modes(self) -> list[str] | None:
        return self._attr_preset_modes

homeassistant.components.fan.FanEntity = FanEntity

import homeassistant.helpers.restore_state
class RestoreEntity(Entity):
    async def async_get_last_state(self):
        return None

homeassistant.helpers.restore_state.RestoreEntity = RestoreEntity

import homeassistant.config_entries
class OptionsFlow:
    def add_suggested_values_to_schema(self, schema, suggested):
        return schema
    def async_show_form(self, step_id, data_schema, errors=None, description_placeholders=None):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}
    def async_create_entry(self, title, data):
        return {"type": "create_entry", "title": title, "data": data}
homeassistant.config_entries.OptionsFlow = OptionsFlow

class ConfigFlow:
    def __init_subclass__(cls, domain=None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._domain = domain

    def add_suggested_values_to_schema(self, schema, suggested):
        return schema

    def async_show_form(self, step_id, data_schema, errors=None, description_placeholders=None):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}
    def async_create_entry(self, title, data):
        return {"type": "create_entry", "title": title, "data": data}
homeassistant.config_entries.ConfigFlow = ConfigFlow
