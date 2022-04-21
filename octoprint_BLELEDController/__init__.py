# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import octoprint.settings
import asyncio
import flask

from .LEDCommand import LEDCommand
from .BLELEDControllerInterface import BLELEDControllerInterface, BLELEDControllerDummyInterface
from .worker_manager import WorkerManager
from .BLEDiscovery import BLEDiscovery, BLEDiscoveryDummy

# FOR DEV PURPOSES, DISABLE ON DEPLOYED PLUGIN
use_dummy_bleled_interface = False

class BLELEDStripControllerPlugin(octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.ShutdownPlugin,
    octoprint.plugin.SimpleApiPlugin
):

    #~~ StartupPlugin mixin
    def on_after_startup(self):
        self._logger.info("BLELEDStripPlugin has started initializing")
        
        if not use_dummy_bleled_interface:
            self.BLE_intf = BLELEDControllerInterface(
                address=self._settings.get(["mac_addr"])
                ,service_UID=self._settings.get(["service_uuid"]),
                logger=self._logger)
            self.BLE_discovery = BLEDiscovery(logger=self._logger)
        else:
            self.BLE_intf = BLELEDControllerDummyInterface(
                address=self._settings.get(["mac_addr"])
                ,service_UID=self._settings.get(["service_uuid"]),
                logger=self._logger)
            self.BLE_discovery = BLEDiscoveryDummy(logger=self._logger)

        self.led_cmd_maker = LEDCommand(start_code=0x7e,end_code=0xef)
        self._logger.debug("Init settings - MAC Address: " + self._settings.get(["mac_addr"]) 
                        + "\nService UUID: " + self._settings.get(["service_uuid"])
                        + "\nLED Strip Config: RGB Hex: " + str(hex(self._settings.get_int(["led_strip", "hex_color"])))
                        + "\n is on: " + str(self._settings.get(["led_strip", "is_on"]))
                        + "\n brightness: " + str(self._settings.get_int(["led_strip", "brightness"]))
        )
        self.worker_mgr = WorkerManager(self)
        # make sure async loop has initialized before proceeding with async method
        while not hasattr(self.worker_mgr, 'loop'):
            pass
        asyncio.run_coroutine_threadsafe(
            self.BLE_intf.connect(), self.worker_mgr.loop
        )
        self._logger.info("BLELEDStripPlugin initialized")

    #~~ ShutdownPlugin mixin
    def on_shutdown(self):
        if self.BLE_intf is not None and self.BLE_intf.is_connected:
            future = asyncio.run_coroutine_threadsafe(
                self.BLE_intf.disconnect()
                ,self.worker_mgr.loop
            )

            # have to block and make sure this finishes
            while not future.done():
                pass

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            mac_addr='aa:bb:cc:dd:ee:ff'
            ,service_uuid='0000fff3-0000-1000-8000-00805f9b34fb'
            ,led_strip=dict(
                hex_color=0xffffff
                ,is_on=True
                ,brightness=100
            )
        )

    ##~~ SettingsPlugin mixin
    def on_settings_save(self, data):
        old_mac_addr = self._settings.get(["mac_addr"])
        old_service_uuid = self._settings.get(["service_uuid"])
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        new_mac_addr = self._settings.get(["mac_addr"])
        new_service_uuid = self._settings.get(["service_uuid"])

        # connection configuration changed, reset required
        if old_mac_addr != new_mac_addr or old_service_uuid != new_service_uuid:
            if not self.BLE_intf.is_connected:
                self.BLE_intf.set_conn_params(
                    dict(
                        address=self._settings.get(["mac_addr"]),
                        service_uuid=self._settings.get(["service_uuid"])
                    )
                )
            else:
                self.BLE_intf.set_conn_params(
                    dict(
                        address=self._settings.get(["mac_addr"]),
                        service_uuid=self._settings.get(["service_uuid"])
                    )
                )
                asyncio.run_coroutine_threadsafe(
                    self.BLE_intf.reconnect(), self.worker_mgr.loop
                )

    #~~ TemplatePlugin mixin
    def get_template_configs(self):
        return [
			dict(type="tab", template="BLELEDController_tab.jinja2"),
			dict(type="settings", template="BLELEDController_settings.jinja2")
		]
   
    #~~ AssetPlugin mixin
    def get_assets(self):
        return dict(
            js=["js/BLELEDController.js", "js/BLELEDControllerSettings.js", "js/jscolor.min.js"],
            css=["css/BLELEDController.css"],
            img=["img/352060_bluetooth_searching_icon.png"]
        )

    #~~ SimpleApiPlugin mixin
    def on_api_command(self, command, data):
        self._logger.debug("POST Command received: " + command + ", with data: " + str(data)) 
        if command == "turn_on":
            self._turn_on(bool(data.get('is_on', None)))
        elif command == 'do_reconnect_task':
            return self.do_reconnect_task() 
        elif self._settings.get(["led_strip", "is_on"]) and (command == "update_color" or command == "update_brightness"):
            if command == "update_color":
                color = data.get('color_hex', None)
                self._update_rgb(color)
            elif command == "update_brightness":
                self._update_brightness(data.get('brightness', None))
        elif not self._settings.get(["led_strip", "is_on"]) and (command == "update_color" or command == "update_brightness"):
                self._logger.debug("Command ignored, led strip is off")
        elif command == 'do_ble_scan_task':
            return self.do_ble_scan_task()
        elif command == 'query_task':
            return self.query_task(data.get('task_id', None))

    ##~~ SimpleApiPlugin hook
    def get_api_commands(self):
        return dict(
		    update_color=["color_hex"]
            ,do_reconnect_task=[]
            ,update_brightness=["brightness"]
            ,turn_on=["is_on"]
            ,do_ble_scan_task=[]
            ,query_task=["task_id"]
        )

    # simple api command handler
    def _update_rgb(self, ui_color):
        color_rgb = int(ui_color, 16)
        if color_rgb == self._settings.get(["led_strip", "hex_color"]):
            self._logger.debug("Update color ignored, no value change.")
            return
        self.on_settings_save(dict(
            led_strip=dict(
                hex_color=color_rgb
                )
        ))
        cmd = self.led_cmd_maker.create_set_color_command(
            r_compo= (color_rgb & 0xff0000) >> 16
            ,g_compo= (color_rgb & 0x00ff00) >> 8
            ,b_compo= color_rgb & 0x0000ff
        )
        asyncio.run_coroutine_threadsafe(
            self.BLE_intf.send_msg(cmd), self.worker_mgr.loop
        )
        self._logger.debug("New color updated: " + str(hex(color_rgb)))

    # simple api command handler
    def _turn_on(self, doTurnOn: bool):
        if doTurnOn is None:
            return
        if doTurnOn == self._settings.get(["led_strip", "is_on"]):
            self._logger.debug("Turn on/off update ignored, no value change.")
            return

        self.on_settings_save(dict(
            led_strip=dict(
                is_on=bool(doTurnOn)
                )
        ))
        cmd = bytearray()
        if doTurnOn:
            cmd = self.led_cmd_maker.create_turn_on_command()
        else:
            cmd = self.led_cmd_maker.create_turn_off_command()

        asyncio.run_coroutine_threadsafe(
                self.BLE_intf.send_msg(cmd), self.worker_mgr.loop
            )
        self._logger.debug("LED strip turned " + ("on" if doTurnOn else "off"))

    # simple api command handler
    def _update_brightness(self, brightness: int):
        if int(brightness) > 100:
            self._logger.debug("LED strip brightness set value (" + str(brightness) + ") exceeds max allowed value (" + str(100) + ")")

        brightness_val = int(brightness) & 0x64 # limit brightness value up to 100 only

        if brightness_val == self._settings.get(["led_strip", "brightness"]):
            self._logger.debug("Update brightness ignored, no value change.")
            return
        
        self.on_settings_save(dict(
            led_strip=dict(
                brightness=brightness_val
                )
        ))
        
        cmd = self.led_cmd_maker.create_set_brightness_command(brightness=self._settings.get(["led_strip", "brightness"]))
        asyncio.run_coroutine_threadsafe(
                self.BLE_intf.send_msg(cmd), self.worker_mgr.loop
            )
        self._logger.debug("LED strip brightness updated to " + str(self._settings.get(["led_strip", "brightness"])))

    # simple api command handler
    def do_reconnect_task(self):
        future = asyncio.run_coroutine_threadsafe(
            self.BLE_intf.reconnect(), self.worker_mgr.loop
        )
        task_id = self.worker_mgr.register_task(future)

        return flask.jsonify(task_id=task_id)

    # simple api command handler
    def do_ble_scan_task(self):
        future = asyncio.run_coroutine_threadsafe(
            self.BLE_discovery.getDevices(redo_scan=True), self.worker_mgr.loop
        )
        task_id = self.worker_mgr.register_task(future)

        return flask.jsonify(task_id=task_id)

    # simple api command handler
    def query_task(self, task_id: str):
        task = self.worker_mgr.get_task(task_id=task_id)
        res = None

        if task is None:
            self._logger.debug(f'query_task: task with id = {task_id} does not exist')
            return None
        if task.done():
            res = task.result()
            self._logger.debug(f'query_task: task with id = {task_id} result: {res}')
            self.worker_mgr.deregister_task(task_id=task_id)
        
        return flask.jsonify(task_running=not task.done(), result=res)

    ##~~ Softwareupdate hook 
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "BLELEDController": {
                "displayName": "Bleledcontroller Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "LBMercado",
                "repo": "OctoPrint-Bleledcontroller",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/LBMercado/OctoPrint-Bleledcontroller/archive/{target_version}.zip",
            }
        }

    ##~~ TemplatePlugin hook
    def get_template_vars(self):
        return dict(
            mac_addr=self._settings.get(["mac_addr"])
            ,service_uuid=self._settings.get(["service_uuid"])
            ,led_strip=dict(
                hex_color=self._settings.get_int(["led_strip", "hex_color"])
                ,is_on=self._settings.get(["led_strip", "is_on"])
                ,brightness=self._settings.get_int(["led_strip", "brightness"])
            )
        )

__plugin_name__ = "BLE LED Controller"
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<6"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = BLELEDStripControllerPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
