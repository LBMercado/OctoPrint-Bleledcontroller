/*
 * View model for OctoPrint-Bleledcontroller
 *
 * Author: Luis Mercado
 * License: AGPLv3
 */
$(function() {
    function BleledcontrollerViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0]
        self.color = ko.observable()

        self.updateColor = function(picker, event) {
            var newColor = event.currentTarget.jscolor.toHEXString()
            if(newColor) {
                self.color(newColor)
            }
        }

        self.onBeforeBinding = function() {
            self.updateColorView(self.settingsViewModel.settings.plugins.BLELEDController.led_strip_hex_color())
        }

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if(plugin != 'BLELEDController') { return }
            if(data.hasOwnProperty('led_strip_hex_color')) {
                self.updateColorView(data.led_strip_hex_color)
            }
        }

        self.updateColorView = function(rcv_color_hex){
            var js_color_input = "".concat('#', rcv_color_hex.toString(16))
            self.color(js_color_input)
            document.querySelector('#color-picker-control').jscolor.fromString(self.color())
        }

        self.applyChanges = function() {
            var color_hex = self.color().substring(1)
            OctoPrint.simpleApiCommand('BLELEDController', 'update_color', {'color_hex': color_hex})
        }
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: BleledcontrollerViewModel,
        dependencies: [ "settingsViewModel" ],
        elements: [ "#tab_plugin_BLELEDController" ]
    });
});
