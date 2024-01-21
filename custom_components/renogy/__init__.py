"""The renogy integration."""
from __future__ import annotations


from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice

from bleak_retry_connector import (
    close_stale_connections_by_address,
    establish_connection,
)
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging
from datetime import timedelta

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

from .renogy.device import getStats

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

# address = "80:6F:B0:0F:BD:C1"
address = None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up renogy from a config entry."""
    global address
    hass.data.setdefault(DOMAIN, {})

    print("starting up renogy")
    # print(entry.data)
    address = entry.data.get("mac")
    # print(address)

    batteryListStr = entry.data.get("batteries")
    batteryList = []
    if "," in batteryListStr:
        batteryList = [int(i) for i in batteryListStr.split(",")]
    else:
        batteryList.append(int(batteryListStr))

    controllerListStr = entry.data.get("controllers")
    controllerList = []
    if "," in controllerListStr:
        controllerList = [int(i) for i in controllerListStr.split(",")]
    else:
        controllerList.append(int(controllerListStr))

    assert address is not None
    await close_stale_connections_by_address(address)
    # print("closed stale connections")

    ble_device = bluetooth.async_ble_device_from_address(hass, address)
    # print("got a device")
    if not ble_device:
        # print("Couldn't connect to device, hopefully it's just gone out for the day...")
        # return False
        raise ConfigEntryNotReady(
            f"Could not find Renogy device with address {address}"
        )
        # return None

    async def _async_update_method() -> dict:
        # else:
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        return await getStats(
            client=client, batteryList=batteryList, controllerList=controllerList
        )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update_method,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][address] = coordinator
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    # hass.states.set(f"{DOMAIN}.world", "Mark")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    print(f"Unloading renogy {address}")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(address)

    return unload_ok
