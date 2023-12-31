"""Polestar API for Polestar integration."""
import logging

from .pypolestar.exception import PolestarApiException, PolestarAuthException

from .pypolestar.polestar import PolestarApi

from urllib3 import disable_warnings

from homeassistant.core import HomeAssistant

POST_HEADER_JSON = {"Content-Type": "application/json"}

_LOGGER = logging.getLogger(__name__)

class DictObj:
    def __init__(self, in_dict:dict):
        assert isinstance(in_dict, dict)
        for key, val in in_dict.items():
            if isinstance(val, (list, tuple)):
                setattr(self, key, [DictObj(x) if isinstance(x, dict) else x for x in val])
            else:
                setattr(self, key, DictObj(val) if isinstance(val, dict) else val)

class Polestar:
    def __init__(self,
                 hass: HomeAssistant,
                 username: str,
                 password: str
                 ) -> None:
        self.id = None
        self.name = "Polestar "
        self.polestarApi = PolestarApi(username, password)
        self.vehicle = DictObj({})
        disable_warnings()

    async def init(self):
        await self.polestarApi.init()
        self.vehicle = DictObj(self.polestarApi.get_vehicle_data())
        if self.vehicle and hasattr(self.vehicle, 'vin'):
            # fill the vin and id in the constructor
            self.id = self.vehicle.vin[:8]
            self.name = "Polestar " + self.vehicle.vin[-4:]

    def get_latest_data(self, query: str, field_name: str):
        return self.polestarApi.get_latest_data(query, field_name)

    def get_latest_call_code(self):
        # if AUTH code last code is not 200 then we return that error code,
        # otherwise just give the call_code in API
        if self.polestarApi.auth.latest_call_code != 200:
            return self.polestarApi.auth.latest_call_code
        return self.polestarApi.latest_call_code

    async def async_update(self) -> None:
        try:
            await self.polestarApi.get_ev_data(self.vehicle.vin)
        except PolestarApiException as e:
            _LOGGER.warning("API Exception on update data %s", str(e))
        except PolestarAuthException as e:
            _LOGGER.warning("Auth Exception on update data %s", str(e))

    def get_value(self, query: str, field_name: str):
        data = self.polestarApi.get_cache_data(query, field_name)
        if data is None:
            return
        return data
