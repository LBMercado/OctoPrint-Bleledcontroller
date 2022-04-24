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
        self.loginStateViewModel = parameters[2];
        self.accessViewModel = parameters[3];

        // binding variables
        self.color = ko.observable();
        self.is_on = ko.observable();
        self.brightness = ko.observable();
        self.webcamDisableTimeout = undefined;
        self.webcamLoaded = ko.observable(false);
        self.webcamMjpgEnabled = ko.observable(false);
        self.webcamError = ko.observable(false);

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

        self.onTabChange = function (current, previous) {
            if (current == "#tab_plugin_BLELEDController") {
                self._enableWebcam();
            } else if (previous == "#tab_plugin_BLELEDController") {
                self._disableWebcam();
            }
        };

        self.onBrowserTabVisibilityChange = function (status) {
            if (status) {
                self._enableWebcam();
            } else {
                self._disableWebcam();
            }
        };

        self.onWebcamLoaded = function () {
            if (self.webcamLoaded()) return;

            log.debug("Webcam stream loaded");
            self.webcamLoaded(true);
            self.webcamError(false);
        };

        self.onWebcamErrored = function () {
            log.debug("Webcam stream failed to load/disabled");
            self.webcamLoaded(false);
            self.webcamError(true);
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

        self._switchToMjpgWebcam = function () {
            var webcamImage = $("#bleled_webcam_image");
            var currentSrc = webcamImage.attr("src");

            // safari bug doesn't release the mjpeg stream, so we just set it up the once
            if (OctoPrint.coreui.browser.safari && currentSrc != undefined) {
                return;
            }

            var newSrc = self.settingsViewModel.webcam_streamUrl();
            if (currentSrc != newSrc) {
                if (self.settingsViewModel.webcam_cacheBuster()) {
                    if (newSrc.lastIndexOf("?") > -1) {
                        newSrc += "&";
                    } else {
                        newSrc += "?";
                    }
                    newSrc += new Date().getTime();
                }

                self.webcamLoaded(false);
                self.webcamError(false);
                webcamImage.attr("src", newSrc);

                self.webcamMjpgEnabled(true);
            }
        };


        self._enableWebcam = function () {
            if (
                OctoPrint.coreui.selectedTab != "#tab_plugin_BLELEDController" ||
                !OctoPrint.coreui.browserTabVisible
            ) {
                return;
            }

            if (self.webcamDisableTimeout != undefined) {
                clearTimeout(self.webcamDisableTimeout);
            }

            // IF disabled then we dont need to do anything
            if (self.settingsViewModel.webcam_webcamEnabled() == false) {
                return;
            }

            // Determine stream type and switch to corresponding webcam.
            var streamType = determineWebcamStreamType(self.settingsViewModel.webcam_streamUrl());
            if (streamType == "mjpg") {
                self._switchToMjpgWebcam();
            } else {
                throw "Unsupported or unknown stream type " + streamType;
            }
        };
        
        self._disableWebcam = function () {
            // only disable webcam stream if tab is out of focus for more than 5s, otherwise we might cause
            // more load by the constant connection creation than by the actual webcam stream

            // safari bug doesn't release the mjpeg stream, so we just disable this for safari.
            if (OctoPrint.coreui.browser.safari) {
                return;
            }

            var timeout = self.settingsViewModel.webcam_streamTimeout() || 5;
            self.webcamDisableTimeout = setTimeout(function () {
                log.debug("Unloading webcam stream");
                $("#bleled_webcam_image").attr("src", "");
                self.webcamLoaded(false);
            }, timeout * 1000);
        };
    };   
    OCTOPRINT_VIEWMODELS.push({
        construct: BleledcontrollerViewModel,
        dependencies: [ "settingsViewModel", "controlViewModel", "loginStateViewModel", "accessViewModel" ],
        elements: [ "#tab_plugin_BLELEDController" ]
    });
});
