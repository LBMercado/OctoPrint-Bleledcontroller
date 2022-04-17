/*
 * View model for OctoPrint-Bleledcontroller
 *
 * Author: Luis Mercado
 * License: AGPLv3
 */
$(function() {
    function BleledcontrollerSettingsViewModel(parameters) {
        var self = this;

        // injected params
        self.settingsViewModel = parameters[0];

        // ko variables
        self.mac_addr = ko.observable();
        self.service_uuid = ko.observable();
        self.show_conn_status = ko.observable(false);

        self.testConn = function() {
            self.show_conn_status(true);
            $('.bleled-status').removeClass(['bleled-status-load-complete', 'bleled-status-load-fail']);
            $('.bleled-status-check').hide();
            $('.bleled-status-fail').hide();

            OctoPrint.simpleApiCommand('BLELEDController', 'do_reconnect')
            .done((res)=>{                
                var is_connected = res.is_connected;
                if (is_connected) {
                    $('.bleled-status').addClass('bleled-status-load-complete');
                    $('.bleled-status-check').show();
                } else {
                    $('.bleled-status').addClass('bleled-status-load-fail');
                    $('.bleled-status-fail').show();
                }
                
            });
        };

        self.bindSettings = function(){
            self.mac_addr(self.settingsViewModel.settings.plugins.BLELEDController.mac_addr());
            self.service_uuid(self.settingsViewModel.settings.plugins.BLELEDController.service_uuid());
        };

        self.onBeforeBinding = function() {
            self.bindSettings();
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if(plugin != 'BLELEDController') { return }
            if(data.hasOwnProperty('mac_addr')) {
                self.mac_addr(data['mac_addr'])
            }
            if(data.hasOwnProperty('service_uuid')){
                self.service_uuid(data['service_uuid'])
            }
        }
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: BleledcontrollerSettingsViewModel,
        dependencies: [ "settingsViewModel" ],
        elements: [ "#settings_plugin_BLELEDController" ]
    });
});
