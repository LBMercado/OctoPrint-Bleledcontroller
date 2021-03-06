from bleak import BleakClient
import asyncio

class BLELEDControllerInterface():
    def __init__(self, address: str, service_UID: str, logger):
        self.address = address.upper()
        self.service_UID = service_UID.lower()
        self.client_conn = None
        self._logger = logger
        self._is_connecting = False
    
    def set_conn_params(self, conn_params: dict):
        if "address" in conn_params.keys():
            self.address = conn_params["address"].upper()
        if "service_UID" in conn_params.keys():
            self.service_UID = conn_params["service_UID"].lower()
    
    async def connect(self):
        if not self._is_connecting:
            self.client_conn = BleakClient(self.address)
            
            try:
                self._is_connecting = True
                await self.client_conn.connect()
            except Exception as e:
                self._logger.debug(e)
                await self.disconnect()
            finally:
                self._is_connecting = False

    def is_connected(self) -> bool:
        if self.client_conn is not None and self.client_conn.is_connected:
            for svc in self.client_conn.services:
                for char in svc.characteristics:
                    # return true only if our set service UUID matches a service UUID available
                    if "read" in char.properties and char.uuid == self.service_UID:
                        return True
            self._logger.debug('current connection has invalid service uuid set')
        return False

    async def disconnect(self):
        if not self._is_connecting:
            self._is_connecting = True
            await self.client_conn.disconnect()
            self._is_connecting = False

    async def send_msg(self, cmd: bytearray):
        if self.is_connected() and not self._is_connecting:
            try:
                await self.client_conn.write_gatt_char(self.service_UID, cmd)
            except Exception as e:
                self._logger.debug(e)

    async def reconnect(self):
        await self.disconnect()
        await self.connect()
        return self.is_connected()

# for testing purposes, do not use
class BLELEDControllerDummyInterface(BLELEDControllerInterface):
    def __init__(self, address: str, service_UID: str, logger = None):
        super().__init__(address, service_UID, logger)
        self._is_connected = False

    def is_connected(self) -> bool:
        return self._is_connected
    
    async def connect(self, do_simulate_failure: bool = False):
        self._logger.debug('connect starting')
        await asyncio.sleep(1)
        self._is_connected = not do_simulate_failure
        self._logger.debug('connect ' + 'done' if not do_simulate_failure else 'failed!')

    async def disconnect(self):
        self._logger.debug('disconnect starting')
        await asyncio.sleep(1)
        self._is_connected = False
        self._logger.debug('disconnect done')

    async def send_msg(self, cmd: bytearray):
        self._logger.debug('send msg starting')
        await asyncio.sleep(1)
        self._logger.debug('send msg done')

    async def reconnect(self, do_simulate_failure: bool = False):
        self._logger.debug('reconnect starting')
        await self.disconnect()
        await self.connect(do_simulate_failure)
        self._logger.debug('reconnect done')
        return self.is_connected()

if __name__ == "__main__":
    intf = BLELEDControllerInterface('','')