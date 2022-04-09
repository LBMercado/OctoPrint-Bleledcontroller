/*
 * View model for OctoPrint-Bleledcontroller
 *
 * Author: Luis Mercado
 * License: AGPLv3
 */
$(function() {
    function BleledcontrollerViewModel(parameters) {
        var self = this;

        // view models
        self.settingsViewModel = parameters[0];
        self.controlViewModel = parameters[1];

        // binding variables
        self.color = ko.observable();
        self.is_on = ko.observable();
        self.brightness = ko.observable();
        self.webcam_streamUrl = ko.computed(function(){
			if(self.settingsViewModel.webcam_streamUrl() !== "") {
				return self.settingsViewModel.webcam_streamUrl();
			} else {
				return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg==";
			}
		});


        // hooks
        self.onBeforeBinding = function() {
            self.updateColorView(self.settingsViewModel.settings.plugins.BLELEDController.led_strip.hex_color());
            self.is_on(self.settingsViewModel.settings.plugins.BLELEDController.led_strip.is_on());
            self.brightness(self.settingsViewModel.settings.plugins.BLELEDController.led_strip.brightness());
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if(plugin != 'BLELEDController') { return }
            if(data.hasOwnProperty('led_strip')) {
                if (data.led_strip.hasOwnProperty('hex_color'))
                    self.updateColorView(data.led_strip.hex_color);
                if (data.led_strip.hasOwnProperty('is_on'))
                    self.is_on(data.led_strip.is_on);
                if (data.led_strip.hasOwnProperty('brightness'))
                    self.brightness(data.led_strip.brightness);
            }
        };

        // custom-defined functions
        self.updateColorView = function(rcv_color_hex){
            var js_color_input = "".concat('#', rcv_color_hex.toString(16));
            self.color(js_color_input);
            document.querySelector('#color-picker-control').jscolor.fromString(self.color());
        }
        
        self.updateColor = function(picker, event) {
            var newColor = event.currentTarget.jscolor.toHEXString()
            if(newColor) {
                self.color(newColor);
            }
        };

        self.applyChanges = function() {
            var color_hex = self.color().substring(1);
            OctoPrint.simpleApiCommand('BLELEDController', 'turn_on', {'is_on': self.is_on()})
            .then(() => {
                if (self.is_on){
                    var promise_1 = OctoPrint.simpleApiCommand('BLELEDController', 'update_color', {'color_hex': color_hex});
                    var promise_2 = OctoPrint.simpleApiCommand('BLELEDController', 'update_brightness', {'brightness': self.brightness()});
                    
                    Promise.all([promise_1, promise_2])
                    .then(() => {
                        OctoPrint.settings.getPluginSettings('BLELEDController')
                        .then((res) => {
                            OctoPrint.settings.savePluginSettings('BLELEDController', res);
                        });
                    })
                } else {
                    OctoPrint.settings.getPluginSettings('BLELEDController')
                        .then((res) => {
                            OctoPrint.settings.savePluginSettings('BLELEDController', res);
                        });
                }
            });
        };
        
    };   
    OCTOPRINT_VIEWMODELS.push({
        construct: BleledcontrollerViewModel,
        dependencies: [ "settingsViewModel", "controlViewModel" ],
        elements: [ "#tab_plugin_BLELEDController" ]
    });
});
