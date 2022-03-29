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
        self.isConnTestOk = ko.observable("Not Started");

        self.testConn = function() {
            OctoPrint.simpleApiCommand('BLELEDController', 'do_reconnect')
            .done((res)=>{
                self.isConnTestOk(res.is_connected ? "Connection successful!" : "Connection failed!");
                showDialog("#settings_simpleDialog", function(dialog){
                    dialog.modal('hide');
                });
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

    function showDialog(dialogId, confirmFunction){
        var myDialog = $(dialogId);
        var confirmButton = $("button.btn-confirm", myDialog);
        var cancelButton = $("button.btn-cancel", myDialog);

        confirmButton.unbind("click");
        confirmButton.bind("click", function() {
            confirmFunction(myDialog);
        });
        myDialog.modal({
        }).css({
            width: 'auto',
            'margin-left': function() { return -($(this).width() /2); }
        });
}
});
