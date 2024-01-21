"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo, CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from random import randint
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
import json

from .const import DOMAIN

# address = "80:6F:B0:0F:BD:C1"

SENSORS_MAPPING_TEMPLATE: dict[str, SensorEntityDescription] = {
    "remainingCapacity": SensorEntityDescription(
        key="remainingCapacity",
        native_unit_of_measurement="Ah",
        name="Remaining Capacity",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "totalCapacity": SensorEntityDescription(
        key="totalCapacity",
        native_unit_of_measurement="Ah",
        name="Total Capacity",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "current": SensorEntityDescription(
        key="current",
        native_unit_of_measurement="A",
        name="Current",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "voltage": SensorEntityDescription(
        key="voltage",
        native_unit_of_measurement="v",
        name="Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "dischargeCurentLimit": SensorEntityDescription(
        key="dischargeCurentLimit",
        native_unit_of_measurement="A",
        name="Discharge Curent Limit",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "chargeCurentLimit": SensorEntityDescription(
        key="chargeCurentLimit",
        native_unit_of_measurement="A",
        name="Charge Curent Limit",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "alternatorVoltage": SensorEntityDescription(
        key="alternatorVoltage",
        native_unit_of_measurement="v",
        name="Alternator Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "alternatorCurrent": SensorEntityDescription(
        key="alternatorCurrent",
        native_unit_of_measurement="A",
        name="Alternator Current",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "alternatorPower": SensorEntityDescription(
        key="alternatorPower",
        native_unit_of_measurement="w",
        name="Alternator Power",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "solarVoltage": SensorEntityDescription(
        key="solarVoltage",
        native_unit_of_measurement="v",
        name="Solar Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "solarCurrent": SensorEntityDescription(
        key="solarCurrent",
        native_unit_of_measurement="A",
        name="Solar Current",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "solarPower": SensorEntityDescription(
        key="solarPower",
        native_unit_of_measurement="w",
        name="Solar Power",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "cell1Voltage": SensorEntityDescription(
        key="cell1Voltage",
        native_unit_of_measurement="v",
        name="Cell 1 Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "cell2Voltage": SensorEntityDescription(
        key="cell2Voltage",
        native_unit_of_measurement="v",
        name="Cell 2 Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "cell3Voltage": SensorEntityDescription(
        key="cell3Voltage",
        native_unit_of_measurement="v",
        name="Cell 3 Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "cell4Voltage": SensorEntityDescription(
        key="cell4Voltage",
        native_unit_of_measurement="v",
        name="Cell 4 Voltage",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "cell1Temperature": SensorEntityDescription(
        key="cell1Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        name="Cell 1 Temperature",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "cell2Temperature": SensorEntityDescription(
        key="cell2Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        name="Cell 2 Temperature",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "cell3Temperature": SensorEntityDescription(
        key="cell3Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        name="Cell 3 Temperature",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "cell4Temperature": SensorEntityDescription(
        key="cell4Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        name="Cell 4 Temperature",
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """Set up the sensor platform."""
    address = config_entry.data.get("mac")
    friendlyName = config_entry.data.get("friendlyName")
    print(f"In sensor: {address}")
    coordinator: DataUpdateCoordinator[str] = hass.data[DOMAIN][address]
    entities = []
    # print(SENSORS_MAPPING_TEMPLATE)
    for device, values in coordinator.data.items():
        for sensor in values:
            # print(SENSORS_MAPPING_TEMPLATE.get(sensor))
            entities.append(
                RenogySensor(
                    coordinator,
                    coordinator,
                    values.get("address"),
                    SENSORS_MAPPING_TEMPLATE.get(sensor),
                    sensor,
                    friendlyName,
                )
            )
    async_add_entities(entities)
    # async_add_entities(
    #     [
    #         BatteryRemainingCapacity(coordinator, coordinator.data, 48)
    #         # BatteryRemainingCapacity(coordinator, coordinator.data, 49),
    #     ]
    # )
    # config_entry.async_on_unload(
    #     # only start after all platforms have had a chance to subscribe
    #     coordinator.async_start()
    # )


class RenogySensor(CoordinatorEntity[DataUpdateCoordinator[str]], SensorEntity):
    """Renogy Sensor"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        renogyList: dict,
        deviceAddress,
        entity_description,
        sensorName: str,
        friendlyName: str,
    ) -> None:
        """init."""
        super().__init__(coordinator)
        self._deviceaddress = deviceAddress
        self._sensorname = sensorName
        self._friendlyName = friendlyName
        self._attr_name = self._sensorname
        # f"Renogy {self._deviceaddress} {sensorName}"
        self._attr_unique_id = f"{self._deviceaddress}_{sensorName}"

        # print(sensorName)
        if entity_description is not None:
            # print(f"entity description for {sensorName}: {entity_description}")
            self.entity_description = entity_description
        else:
            print(f"No entity description for {sensorName}")

        # self._attr_device_info = DeviceInfo(
        #     connections={
        #         (
        #             CONNECTION_BLUETOOTH,
        #             self._deviceaddress,
        #         )
        #     },
        #     name=f"Renogy Name {self._deviceaddress}",
        #     manufacturer="Renogy",
        #     model="Renogy model",
        # )

    _deviceaddress = ""
    _sensorname = ""
    _attr_has_entity_name = True
    # _attr_name = "Battery Remaining Capacity"
    # _attr_native_unit_of_measurement = "Ah"
    # _attr_suggested_display_precision = 2
    # _attr_device_class = SensorDeviceClass.ENERGY_STORAGE
    # _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self) -> None:
        """Return the state of the sensor."""
        # print(self._deviceaddress, self._sensorname)
        # print(self.coordinator.data.get(self._deviceaddress).get(self._sensorname))
        return self.coordinator.data.get(self._deviceaddress).get(self._sensorname)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._deviceaddress)
            },
            connections={
                (
                    CONNECTION_BLUETOOTH,
                    self._deviceaddress,
                )
            },
            name=f"Renogy {self._friendlyName} {self._deviceaddress}",
            #     name=f"Renogy Name {self._deviceaddress}",
            manufacturer="Renogy",
            model="Renogy model",
            # manufacturer=self.light.manufacturername,
            # model=self.light.productname,
            # sw_version=self.light.swversion,
            # via_device=(hue.DOMAIN, self.api.bridgeid),
        )
