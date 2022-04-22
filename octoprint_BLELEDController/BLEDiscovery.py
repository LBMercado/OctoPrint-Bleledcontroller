import asyncio
from bleak import discover, BleakClient
from .BLELEDControllerInterface import BLELEDControllerDummyInterface, BLELEDControllerInterface

class BLEDiscovery:
    def __init__(self, logger):
        self.device_list = []
        self._logger = logger
    
    async def _lookupDevices(self):
        try:
            devices = await discover()
            self.device_list = [{'name': dev.name, 'address': dev.address} for dev in devices]
            self._logger.debug('BLEDiscovery scanned devices: ' + str(self.device_list))
            # fetch uuid and descriptor info
            for device_info in self.device_list:
                service_uuids, descriptors = await self.discoverDevServices(address=device_info['address'])

                device_info['service_uuids'] = service_uuids
                device_info['descriptors'] = descriptors
        except Exception as e:
            self._logger.debug('BLEDiscovery encountered ERROR during lookupDevices')
            self._logger.debug(e)

    async def getDevices(self, redo_scan = False, active_client: BLELEDControllerInterface = None):
        if not redo_scan and self.device_list:
            return self.device_list
        
        # disconnect active client (if passed)
        if active_client is not None and active_client.is_connected:
            await active_client.disconnect()
        
        await self._lookupDevices()
        
        # reconnect active client (if passed)
        if active_client is not None and not active_client.is_connected:
            await active_client.connect()

        return self.device_list

    async def discoverDevServices(self, address: str = None, client: BleakClient = None):
        uuid_list = []
        descriptor_list = []

        try:
            if client is not None and client.is_connected:
                for service in client.services:
                    for char in service.characteristics:
                        if "read" in char.properties:
                            uuid_list.append(char.uuid)

                        for descriptor in char.descriptors:
                            descriptor_list.append(descriptor.handle)
                self._logger.debug('BLEDiscovery scanned services for \'{address}\'. UUIDs: ' + str(uuid_list) + '\n'
                                + 'descriptors: ' + str(descriptor_list))
                return (uuid_list, descriptor_list)
            
            async with BleakClient(address) as client_adhoc:
                if not client_adhoc.is_connected:
                    self._logger.debug('BLEDiscovery encountered ERROR during discoverDevServices - client is not connected')
                    return (uuid_list, descriptor_list)

                for service in client_adhoc.services:
                    for char in service.characteristics:
                        if "read" in char.properties:
                            uuid_list.append(char.uuid)

                        for descriptor in char.descriptors:
                            descriptor_list.append(descriptor.handle)
                self._logger.debug('BLEDiscovery scanned services for \'{address}\'. UUIDs: ' + str(uuid_list) + '\n'
                                + 'descriptors: ' + str(descriptor_list))
                return (uuid_list, descriptor_list)
        except Exception as e:
            self._logger.debug('BLEDiscovery encountered ERROR during discoverDevServices')
            self._logger.debug(e)
            return (uuid_list, descriptor_list)


class BLEDiscoveryDummy(BLEDiscovery):
    def __init__(self, logger):
        super().__init__(logger)

    async def _lookupDevices(self, simulate_none_found = False):
        await asyncio.sleep(5)
        self.device_list = [
            {
                'address': '24:71:89:CC:09:05',
                'name': 'CC2650 SensorTag',
                'service_uuids': ['b1d0cac0-d50d-11e8-b57b-ccaf789d94a0', '376c7ffc-bfe6-11ec-9d64-0242ac120002'],
                'descriptors':['0x0028', '0x0024']
            },
            {
                'address': '4D:41:D5:8C:7A:0B',
                'name': 'Apple, Inc. Dummy',
                'service_uuids': ['b1d0dad0-d50d-11e8-b57b-ccaf789d94a0', '376c7ffc-bfe6-11ec-9d64-0242ac120004'],
                'descriptors':['0x0023', '0x0025']
            },
            {
                'address': '4D:22:EF:8C:7A:2B',
                'name': 'Another Dummy',
                'service_uuids': ['3767cffc-bfe6-11ec-9d64-0242ac120004'],
                'descriptors':['0x0025']
            }
        ] if not simulate_none_found else []

    async def getDevices(self, redo_scan = False, active_client: BLELEDControllerDummyInterface = None):
        if not redo_scan and self.device_list:
            return self.device_list
        
        # disconnect active client (if passed)
        if active_client is not None and active_client.is_connected:
            await active_client.disconnect()
        
        await self._lookupDevices()
        
        # reconnect active client (if passed)
        if active_client is not None and not active_client.is_connected:
            await active_client.connect()

        return self.device_list

    async def discoverDevServices(self, address: str = None, client: BleakClient = None, simulate_failure = False):
        uuid_list = []
        descriptor_list = []

        await asyncio.sleep(5)

        if simulate_failure:
            return (uuid_list, descriptor_list)

        uuid_list = ['b1d0cac0-d50d-11e8-b57b-ccaf789d94a0', '376c7ffc-bfe6-11ec-9d64-0242ac120002']
        descriptor_list= ['0x0028', '0x0024']

        return (uuid_list, descriptor_list)