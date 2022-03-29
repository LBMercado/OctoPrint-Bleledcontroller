# OctoPrint-Bleledcontroller

This plugin controls cheap 12V LED strips via BLE (Bluetooth Low Energy) using Bleak Python package. [Learn more about this package here](https://bleak.readthedocs.io/en/latest/)

Inspired by a [repository](https://github.com/FergusInLondon/ELK-BLEDOM) I found digging around how to communicate with these 12V LED Strips which conveniently also used the same ELK-BLEDOM bluetooth RGB controller.

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/LBMercado/OctoPrint-Bleledcontroller/archive/master.zip

Bluetooth services require root permissions by default, you can get around that permission issue by providing your OctoPrint user, (pi user), the permissions necessary to be able to use them.

Modify the bluetooth configuration in your Raspberry Pi

    sudo nano /etc/dbus-1/system.d/bluetooth.conf

Paste this config code into the configuration, between the <busconfig> tags

    <policy user="pi">
        <allow send_destination="org.bluez"/>
        <allow send_interface="org.bluez.Agent1"/>
        <allow send_interface="org.bluez.GattCharacteristic1"/>
        <allow send_interface="org.bluez.GattDescriptor1"/>
        <allow send_interface="org.freedesktop.DBus.ObjectManager"/>
        <allow send_interface="org.freedesktop.DBus.Properties"/>
    </policy>

[View here for reference]https://forums.raspberrypi.com/viewtopic.php?t=108581)

## Configuration

You will need to know the MAC address of the bluetooth device in question, though I could implement an auto-scanner in the future, for now it is manually set.
For the service UUID to use, it should be the same like in the repository I based this project from. If not, you can make use of Bleak to find out the service UUID of the device in question.

## Raw code snippet for testing the bluetooth functionality

    import asyncio
    from bleak import BleakClient
    import time

    address = "<Provide-MAC-address-here>"
    service_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
    red_command = bytearray([0x7E, 0x00, 0x05, 0x03, 0xFF, 0x00, 0x00, 0x00, 0xEF])
    white_command = bytearray([0x7E, 0x00, 0x05, 0x03, 0xFF, 0xFF, 0xFF, 0x00, 0xEF])

    async def main(address):
        client = BleakClient(address)
        try:
            await client.connect()
            await client.write_gatt_char(service_UUID, red_command)
            time.sleep(5)
            await client.write_gatt_char(service_UUID, white_command)
        except Exception as e:
            print(e)
        finally:
            await client.disconnect()

    asyncio.run(main(address))exit
