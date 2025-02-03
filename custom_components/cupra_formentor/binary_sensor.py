from . import CupraWeConnectEntity

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up binary sensors for Cupra We Connect."""
    we_connect: weconnect_cupra.WeConnect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    await coordinator.async_config_entry_first_refresh()

    entities = [CupraBinarySensor(sensor, we_connect, coordinator, index)
                for index, vehicle in enumerate(coordinator.data)
                for sensor in SENSORS]

    if entities:
        async_add_entities(entities)

class CupraBinarySensor(CupraWeConnectEntity, BinarySensorEntity):
    """Representation of a Cupra We Connect binary sensor."""

    entity_description: CupraBinaryEntityDescription

    def __init__(
        self,
        sensor: CupraBinaryEntityDescription,
        we_connect: weconnect_cupra.WeConnect,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize Cupra We Connect binary sensor."""
        super().__init__(we_connect, coordinator, index)
        self.entity_description = sensor
        self._attr_name = f"{self.data.nickname} {sensor.name}"
        self._attr_unique_id = f"{self.data.vin}-{sensor.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        try:
            state = self.entity_description.value(self.data.domains)
            if isinstance(state, bool):
                return state
            return get_object_value(state) == get_object_value(self.entity_description.on_value)
        except KeyError:
            return None
