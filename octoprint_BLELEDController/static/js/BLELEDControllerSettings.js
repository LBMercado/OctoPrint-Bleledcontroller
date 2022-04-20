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
        self.devScanList = ko.observable([]);
        self.selectedLookupDevice = ko.observable();
        self.is_scan_started = ko.observable(false);

        // others
        self.query_freq_ms = 750;

        // init ui variables
        self.onStartup = function () {
            self.deviceLookupDialog = $("#bleled_settings_dev_lookup");
            self.deviceLookupBtn = $("#bleled_lookup_dev_btn");
            self.bleledStatus = $('.bleled-status');
            self.bleledStatusCheck = $('.bleled-status-check');
            self.bleledStatusFail = $('.bleled-status-fail');
        };

        self.testConn = function() {
            self.show_conn_status(true);
            self.bleledStatus.removeClass(['bleled-status-load-complete', 'bleled-status-load-fail']);
            self.bleledStatusCheck.hide();
            self.bleledStatusFail.hide();

            OctoPrint.simpleApiCommand('BLELEDController', 'do_reconnect')
            .done((res)=>{                
                var is_connected = res.is_connected;
                if (is_connected) {
                    self.bleledStatus.addClass('bleled-status-load-complete');
                    self.bleledStatusCheck.show();
                } else {
                    self.bleledStatus.addClass('bleled-status-load-fail');
                    self.bleledStatusFail.show();
                }
                
            });
        };

        self.openDevLookup = function() {
            self.deviceLookupDialog.modal({
                minHeight: function () {
                    return Math.max($.fn.modal.defaults.maxHeight() - 80, 250);
                },
                show: true
            });
        };

        self.doDevLookup = function(){
            // animate the button to notify user that we are scanning
            self.deviceLookupBtn.addClass('spinning');
            self.deviceLookupBtn.text("Scanning...");
            self.is_scan_started(true);

            // send scan command to plugin
            OctoPrint.simpleApiCommand('BLELEDController', 'do_ble_scan_task')
            .done((res)=>{                
                if (res !== null) {
                    var task_id = res.task_id;

                    OctoPrint.simpleApiCommand('BLELEDController', 'query_task', {'task_id': task_id})
                    .done((res) => {
                        var is_task_done = !res.task_running;
                        var task_res = res.result;
                        self._doDevLookupQuery(task_id, is_task_done, task_res);
                    });
                } else {
                    // stop scanning animation
                    self.deviceLookupBtn.removeClass('spinning')
                    self.deviceLookupBtn.text("Scan");
                }
            });
        };

        self._doDevLookupQuery = function(task_id, is_task_done, task_res){
            if (is_task_done){
                
                var dev_list = task_res.map(
                    (val) => {
                        return  {
                            'name': val.name,
                            'addr': val.address,
                            'service_uuids': val.service_uuids,
                            'selected_uuid': null
                        };
                    }
                );
                self.devScanList(dev_list);
                // stop scanning animation
                self.deviceLookupBtn.removeClass('spinning')
                self.deviceLookupBtn.text("Scan");
                return;
            }
            
            OctoPrint.simpleApiCommand('BLELEDController', 'query_task', {'task_id': task_id})
            .done((res) => {
                if (res === null){
                    return;
                }
                if (!res.task_running){
                    self._doDevLookupQuery(task_id, !res.task_running, res.result)
                } else {
                    setTimeout(() => {
                        self._doDevLookupQuery(task_id, !res.task_running, res.result)
                    }, self.query_freq_ms);
                };                
            });
        };

        self.confirmDevLookup = function(){
            if (self.selectedLookupDevice() !== null){
                // propagate setting values
                self.mac_addr(self.selectedLookupDevice().addr);
                self.service_uuid(self.selectedLookupDevice().selected_uuid !== null ? self.selectedLookupDevice().selected_uuid : self.service_uuid());
            };
            self.deviceLookupDialog.modal('hide');
        };

        self.cancelDevLookup = function(){
            self.selectedLookupDevice(null);
            self.deviceLookupDialog.modal('hide');
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
        };

        self.onDeviceRowClick = function(row){
            self.selectedLookupDevice(row);
        };

        self.onSettingsBeforeSave = function() {
            self.settingsViewModel.settings.plugins.BLELEDController.mac_addr(self.mac_addr());
            self.settingsViewModel.settings.plugins.BLELEDController.service_uuid(self.service_uuid());
        };

        self.isDeviceRowSelected = function(row){
            if (self.selectedLookupDevice() == null || row == null) {
                return false;
            }

            if (self.selectedLookupDevice().addr == row.addr &&
                  self.selectedLookupDevice().name == row.name &&
                  self.selectedLookupDevice().service_uuids == row.service_uuids){
                return true;
            }
            return false;
        }
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: BleledcontrollerSettingsViewModel,
        dependencies: [ "settingsViewModel" ],
        elements: [ "#settings_plugin_BLELEDController" ]
    });
});
